import py_trees
import carla
import math
import numpy as np

from srunner.scenarios.basic_scenario import BasicScenario
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import WaypointFollower
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import DriveDistance
from srunner.scenariomanager.scenarioatomics.atomic_criteria import (
    IntersectionCollisionLeftTurnBrakeCriterion,
    IntersectionCollisionLeftTurnResumeCriterion,
    MinTTCAutoCriterion,
)


def get_actor_speed(actor):
    v = actor.get_velocity()
    return math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)


def distance_2d(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def make_forward_velocity(actor, speed):
    transform = actor.get_transform()
    yaw = math.radians(transform.rotation.yaw)
    return carla.Vector3D(
        math.cos(yaw) * speed,
        math.sin(yaw) * speed,
        0.0,
    )


class EgoInitialVelocitySetter(py_trees.behaviour.Behaviour):
    def __init__(
        self,
        ego_vehicle,
        target_speed=10.0,
        duration=0.8,
        name="EgoInitialVelocitySetter",
    ):
        super(EgoInitialVelocitySetter, self).__init__(name)
        self.ego_vehicle = ego_vehicle
        self.target_speed = float(target_speed)
        self.duration = float(duration)
        self._start_time = None

    @staticmethod
    def _get_sim_time():
        world = CarlaDataProvider.get_world()
        if world is None:
            return None
        snapshot = world.get_snapshot()
        if snapshot is None:
            return None
        return snapshot.timestamp.elapsed_seconds

    def initialise(self):
        self._start_time = self._get_sim_time()

    def update(self):
        if not self.ego_vehicle or not self.ego_vehicle.is_alive:
            return py_trees.common.Status.FAILURE

        now = self._get_sim_time()
        if self._start_time is None:
            self._start_time = now

        elapsed = 0.0 if now is None or self._start_time is None else now - self._start_time

        if elapsed <= self.duration:
            self.ego_vehicle.set_target_velocity(make_forward_velocity(self.ego_vehicle, self.target_speed))
            return py_trees.common.Status.RUNNING

        return py_trees.common.Status.SUCCESS


class EgoSpeedControl(py_trees.behaviour.Behaviour):
    def __init__(
        self,
        ego_vehicle,
        target_speed=10.0,
        throttle_gain=0.20,
        brake_gain=0.10,
        max_throttle=1.0,
        max_brake=0.50,
        enable_takeover_detection=True,
        takeover_steer_threshold=0.001,
        takeover_throttle_threshold=0.001,
        takeover_brake_threshold=0.001,
        hold_method="target_velocity",
        name="EgoSpeedControl",
    ):
        super(EgoSpeedControl, self).__init__(name)
        self.ego_vehicle = ego_vehicle
        self.target_speed = float(target_speed)
        self.throttle_gain = float(throttle_gain)
        self.brake_gain = float(brake_gain)
        self.max_throttle = float(max_throttle)
        self.max_brake = float(max_brake)
        self.enable_takeover_detection = bool(enable_takeover_detection)
        self.takeover_steer_threshold = float(takeover_steer_threshold)
        self.takeover_throttle_threshold = float(takeover_throttle_threshold)
        self.takeover_brake_threshold = float(takeover_brake_threshold)
        self.hold_method = str(hold_method).strip().lower()
        if self.hold_method not in ("target_velocity", "control"):
            self.hold_method = "target_velocity"
        self._taken_over = False
        self._last_applied_control = None
        self._has_applied_control = False
        self._has_set_initial_velocity = False

    @staticmethod
    def _copy_control(control):
        copied = carla.VehicleControl()
        copied.throttle = float(control.throttle)
        copied.steer = float(control.steer)
        copied.brake = float(control.brake)
        copied.hand_brake = bool(control.hand_brake)
        copied.reverse = bool(control.reverse)
        copied.manual_gear_shift = bool(control.manual_gear_shift)
        copied.gear = int(control.gear)
        return copied

    def _control_changed_from_last_applied(self, current_control):
        if self._last_applied_control is None:
            return False

        last = self._last_applied_control
        if abs(current_control.steer - last.steer) > self.takeover_steer_threshold:
            return True
        if abs(current_control.throttle - last.throttle) > self.takeover_throttle_threshold:
            return True
        if abs(current_control.brake - last.brake) > self.takeover_brake_threshold:
            return True
        if bool(current_control.hand_brake) != bool(last.hand_brake):
            return True
        if bool(current_control.reverse) != bool(last.reverse):
            return True
        if bool(current_control.manual_gear_shift) != bool(last.manual_gear_shift):
            return True
        return False

    def _has_external_input(self, current_control):
        return (
            abs(current_control.steer) > self.takeover_steer_threshold or
            current_control.throttle > self.takeover_throttle_threshold or
            current_control.brake > self.takeover_brake_threshold or
            bool(current_control.hand_brake) or
            bool(current_control.reverse) or
            bool(current_control.manual_gear_shift)
        )

    def _release_control(self):
        self._taken_over = True
        return py_trees.common.Status.SUCCESS

    def update(self):
        if not self.ego_vehicle or not self.ego_vehicle.is_alive:
            return py_trees.common.Status.FAILURE

        if self._taken_over:
            return py_trees.common.Status.SUCCESS

        if not self._has_set_initial_velocity:
            self.ego_vehicle.set_target_velocity(make_forward_velocity(self.ego_vehicle, self.target_speed))
            self._has_set_initial_velocity = True

        current_control = self.ego_vehicle.get_control()

        if self.enable_takeover_detection:
            if self.hold_method == "target_velocity":
                if self._has_external_input(current_control):
                    return self._release_control()
            else:
                if not self._has_applied_control:
                    if self._has_external_input(current_control):
                        return self._release_control()
                else:
                    if self._control_changed_from_last_applied(current_control):
                        return self._release_control()

        if self.hold_method == "target_velocity":
            self.ego_vehicle.set_target_velocity(make_forward_velocity(self.ego_vehicle, self.target_speed))
            return py_trees.common.Status.RUNNING

        current_speed = get_actor_speed(self.ego_vehicle)
        speed_error = self.target_speed - current_speed

        new_control = carla.VehicleControl()
        new_control.steer = current_control.steer
        new_control.hand_brake = False
        new_control.reverse = False
        new_control.manual_gear_shift = False

        if speed_error >= 0.0:
            throttle_cmd = np.clip(speed_error * self.throttle_gain, 0.0, self.max_throttle)
            new_control.throttle = float(throttle_cmd)
            new_control.brake = 0.0
        else:
            brake_cmd = np.clip((-speed_error) * self.brake_gain, 0.0, self.max_brake)
            new_control.throttle = 0.0
            new_control.brake = float(brake_cmd)

        self.ego_vehicle.apply_control(new_control)
        self._last_applied_control = self._copy_control(new_control)
        self._has_applied_control = True
        return py_trees.common.Status.RUNNING


class EgoTriggerOrNearConflict(py_trees.behaviour.Behaviour):
    def __init__(
        self,
        ego_vehicle,
        trigger_location,
        collision_location,
        trigger_distance=4.0,
        conflict_trigger_distance=0.0,
        enable_passed_trigger=True,
        route_direction_x=1.0,
        lateral_tolerance=5.0,
        name="EgoTriggerOrNearConflict",
    ):
        super(EgoTriggerOrNearConflict, self).__init__(name)
        self.ego_vehicle = ego_vehicle
        self.trigger_location = trigger_location
        self.collision_location = collision_location
        self.trigger_distance = float(trigger_distance)
        self.conflict_trigger_distance = float(conflict_trigger_distance)
        self.enable_passed_trigger = bool(enable_passed_trigger)
        self.route_direction_x = 1.0 if float(route_direction_x) >= 0.0 else -1.0
        self.lateral_tolerance = float(lateral_tolerance)

    def update(self):
        if not self.ego_vehicle or not self.ego_vehicle.is_alive:
            return py_trees.common.Status.FAILURE

        ego_loc = self.ego_vehicle.get_location()
        dist_to_trigger = distance_2d(ego_loc, self.trigger_location)
        dist_to_conflict = distance_2d(ego_loc, self.collision_location)

        if dist_to_trigger <= self.trigger_distance:
            return py_trees.common.Status.SUCCESS

        if self.enable_passed_trigger:
            passed_trigger_x = (ego_loc.x - self.trigger_location.x) * self.route_direction_x >= 0.0
            close_to_route_y = abs(ego_loc.y - self.trigger_location.y) <= self.lateral_tolerance
            if passed_trigger_x and close_to_route_y:
                return py_trees.common.Status.SUCCESS

        if self.conflict_trigger_distance > 0.0 and dist_to_conflict <= self.conflict_trigger_distance:
            return py_trees.common.Status.SUCCESS

        return py_trees.common.Status.RUNNING


class AdaptiveNPCInitialSpeed(py_trees.behaviour.Behaviour):
    def __init__(
        self,
        ego_vehicle,
        npc_vehicle,
        waypoint_follower,
        npc_plan_to_collision,
        collision_location,
        min_ego_speed=0.5,
        npc_min_speed=2.0,
        npc_max_speed=25.0,
        npc_speed_scale=1.0,
        npc_arrival_time_margin=0.0,
        name="AdaptiveNPCInitialSpeed",
    ):
        super(AdaptiveNPCInitialSpeed, self).__init__(name)
        self.ego_vehicle = ego_vehicle
        self.npc_vehicle = npc_vehicle
        self.waypoint_follower = waypoint_follower
        self.npc_plan_to_collision = npc_plan_to_collision
        self.collision_location = collision_location
        self.min_ego_speed = float(min_ego_speed)
        self.npc_min_speed = float(npc_min_speed)
        self.npc_max_speed = float(npc_max_speed)
        self.npc_speed_scale = float(npc_speed_scale)
        self.npc_arrival_time_margin = float(npc_arrival_time_margin)
        self._computed = False
        self._computed_speed = None

    def _get_npc_path_length_to_collision(self):
        if not self.npc_vehicle or not self.npc_vehicle.is_alive:
            return 0.0

        current_loc = self.npc_vehicle.get_location()
        length = 0.0
        prev_loc = current_loc

        for wp, _ in self.npc_plan_to_collision:
            loc = wp.transform.location
            length += distance_2d(prev_loc, loc)
            prev_loc = loc

        direct_distance = distance_2d(current_loc, self.collision_location)
        return max(length, direct_distance)

    def _apply_speed_to_waypoint_follower(self, speed):
        for attr_name in ("_target_speed", "target_speed", "_speed", "speed"):
            if hasattr(self.waypoint_follower, attr_name):
                setattr(self.waypoint_follower, attr_name, speed)

        local_planner = getattr(self.waypoint_follower, "_local_planner", None)
        if local_planner is not None and hasattr(local_planner, "set_speed"):
            local_planner.set_speed(speed * 3.6)

    def update(self):
        if self._computed:
            return py_trees.common.Status.SUCCESS

        if (
            not self.ego_vehicle or not self.ego_vehicle.is_alive or
            not self.npc_vehicle or not self.npc_vehicle.is_alive
        ):
            return py_trees.common.Status.FAILURE

        ego_loc = self.ego_vehicle.get_location()
        ego_speed_raw = get_actor_speed(self.ego_vehicle)
        ego_speed = max(ego_speed_raw, self.min_ego_speed)
        ego_distance_to_collision = max(distance_2d(ego_loc, self.collision_location), 0.5)
        ego_time_to_collision = ego_distance_to_collision / ego_speed
        npc_distance_to_collision = self._get_npc_path_length_to_collision()
        available_time = max(ego_time_to_collision + self.npc_arrival_time_margin, 0.1)
        raw_npc_speed = (npc_distance_to_collision / available_time) * self.npc_speed_scale
        adaptive_npc_speed = float(np.clip(raw_npc_speed, self.npc_min_speed, self.npc_max_speed))

        self._apply_speed_to_waypoint_follower(adaptive_npc_speed)
        self._computed_speed = adaptive_npc_speed
        self._computed = True
        return py_trees.common.Status.SUCCESS


class IntersectionCollisionLeftTurn(BasicScenario):
    def __init__(
        self,
        world,
        ego_vehicles,
        config,
        randomize=False,
        debug_mode=False,
        criteria_enable=True,
        timeout=60,
    ):
        def get_param(name, default):
            return config.other_parameters.get(name, {}).get("value", default)

        def get_bool_param(name, default):
            value = str(get_param(name, default)).strip().lower()
            return value in ("true", "1", "yes", "y", "on")

        self._init_speed = float(get_param("init_speed", 10.0))
        self._ego_initial_speed_duration = float(get_param("ego_initial_speed_duration", 0.0))
        self._ego_speed_control = get_bool_param("ego_speed_control", True)
        self._ego_speed_control_takeover_detection = get_bool_param(
            "ego_speed_control_takeover_detection",
            True,
        )
        self._ego_speed_hold_method = str(get_param("ego_speed_hold_method", "target_velocity")).strip()
        self._ego_takeover_steer_threshold = float(get_param("ego_takeover_steer_threshold", 0.001))
        self._ego_takeover_throttle_threshold = float(get_param("ego_takeover_throttle_threshold", 0.001))
        self._ego_takeover_brake_threshold = float(get_param("ego_takeover_brake_threshold", 0.001))
        self._npc_speed = float(get_param("npc_speed", 8.0))
        self._adaptive_npc_speed = get_bool_param("adaptive_npc_speed", True)
        self._trigger_npc_point = carla.Location(
            x=float(get_param("npc_trigger_x", -12.2)),
            y=float(get_param("npc_trigger_y", 205.1)),
            z=float(get_param("npc_trigger_z", 0.7)),
        )
        self._npc_trigger_distance = float(get_param("npc_trigger_distance", 4.0))
        self._collision_location = carla.Location(
            x=float(get_param("collision_x", 43.2)),
            y=float(get_param("collision_y", 205.3)),
            z=float(get_param("collision_z", 0.5)),
        )
        self._conflict_trigger_distance = float(get_param("conflict_trigger_distance", 0.0))
        self._npc_enable_passed_trigger = get_bool_param("npc_enable_passed_trigger", True)
        self._npc_trigger_lateral_tolerance = float(get_param("npc_trigger_lateral_tolerance", 5.0))
        self._min_ego_speed = float(get_param("min_ego_speed", 0.5))
        self._npc_min_speed = float(get_param("npc_min_speed", 2.0))
        self._npc_max_speed = float(get_param("npc_max_speed", 25.0))
        self._npc_speed_scale = float(get_param("npc_speed_scale", 1.0))
        self._npc_arrival_time_margin = float(get_param("npc_arrival_time_margin", 0.0))

        super(IntersectionCollisionLeftTurn, self).__init__(
            "IntersectionCollisionLeftTurn",
            ego_vehicles,
            config,
            world,
            debug_mode,
            criteria_enable=criteria_enable,
        )

        self.scenario_type = "IntersectionCollisionLeftTurn"

        if self.ego_vehicles and self.ego_vehicles[0]:
            ego = self.ego_vehicles[0]
            ego.set_target_velocity(make_forward_velocity(ego, self._init_speed))

    def _initialize_actors(self, config):
        for actor_conf in config.other_actors:
            actor = CarlaDataProvider.request_new_actor(actor_conf.model, actor_conf.transform)
            if actor:
                actor.set_light_state(
                    carla.VehicleLightState(
                        carla.VehicleLightState.Position |
                        carla.VehicleLightState.LowBeam
                    )
                )
                self.other_actors.append(actor)

        if self.ego_vehicles:
            ego = self.ego_vehicles[0]
            ego.set_light_state(
                carla.VehicleLightState(
                    carla.VehicleLightState.Position |
                    carla.VehicleLightState.LowBeam
                )
            )

    def _create_behavior(self):
        all_traffic_lights = CarlaDataProvider.get_world().get_actors().filter("*traffic_light*")
        for light in all_traffic_lights:
            light.set_state(carla.TrafficLightState.Green)
            light.set_green_time(1000.0)

        root = py_trees.composites.Parallel(
            "IntersectionCollisionLeftTurnBehavior",
            policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL,
        )

        if not self.ego_vehicles or len(self.other_actors) < 1:
            return root

        ego = self.ego_vehicles[0]
        left_car = self.other_actors[0]

        if self._ego_initial_speed_duration > 0.0:
            root.add_child(
                EgoInitialVelocitySetter(
                    ego,
                    target_speed=self._init_speed,
                    duration=self._ego_initial_speed_duration,
                )
            )

        if self._ego_speed_control:
            root.add_child(
                EgoSpeedControl(
                    ego,
                    target_speed=self._init_speed,
                    enable_takeover_detection=self._ego_speed_control_takeover_detection,
                    takeover_steer_threshold=self._ego_takeover_steer_threshold,
                    takeover_throttle_threshold=self._ego_takeover_throttle_threshold,
                    takeover_brake_threshold=self._ego_takeover_brake_threshold,
                    hold_method=self._ego_speed_hold_method,
                )
            )

        npc_sequence = py_trees.composites.Sequence("NPCSequence")

        trigger = EgoTriggerOrNearConflict(
            ego_vehicle=ego,
            trigger_location=self._trigger_npc_point,
            collision_location=self._collision_location,
            trigger_distance=self._npc_trigger_distance,
            conflict_trigger_distance=self._conflict_trigger_distance,
            enable_passed_trigger=self._npc_enable_passed_trigger,
            route_direction_x=1.0,
            lateral_tolerance=self._npc_trigger_lateral_tolerance,
            name="TriggerDistanceOrConflictApproach",
        )

        amap = CarlaDataProvider.get_map()
        entry_loc = carla.Location(x=24.5, y=185.4, z=0.5)
        end_loc = self._collision_location
        custom_plan = []
        npc_plan_to_collision = []
        p0 = entry_loc
        p1 = carla.Location(x=24.5, y=self._collision_location.y, z=0.5)
        p2 = end_loc

        for i in range(1, 40):
            t = i / 40.0
            x = (1.0 - t) ** 2 * p0.x + 2.0 * (1.0 - t) * t * p1.x + t ** 2 * p2.x
            y = (1.0 - t) ** 2 * p0.y + 2.0 * (1.0 - t) * t * p1.y + t ** 2 * p2.y
            loc = carla.Location(x=x, y=y, z=0.5)
            wp = amap.get_waypoint(loc, project_to_road=True)
            wp.transform.location = loc
            plan_item = (wp, 0)
            npc_plan_to_collision.append(plan_item)
            custom_plan.append(plan_item)

        for j in range(1, 80):
            loc = carla.Location(x=end_loc.x + j, y=end_loc.y, z=0.5)
            wp = amap.get_waypoint(loc, project_to_road=True)
            wp.transform.location = loc
            custom_plan.append((wp, 4))

        npc_move = WaypointFollower(
            left_car,
            self._npc_speed,
            plan=custom_plan,
        )

        npc_sequence.add_child(trigger)

        if self._adaptive_npc_speed:
            npc_sequence.add_child(
                AdaptiveNPCInitialSpeed(
                    ego_vehicle=ego,
                    npc_vehicle=left_car,
                    waypoint_follower=npc_move,
                    npc_plan_to_collision=npc_plan_to_collision,
                    collision_location=self._collision_location,
                    min_ego_speed=self._min_ego_speed,
                    npc_min_speed=self._npc_min_speed,
                    npc_max_speed=self._npc_max_speed,
                    npc_speed_scale=self._npc_speed_scale,
                    npc_arrival_time_margin=self._npc_arrival_time_margin,
                )
            )

        npc_sequence.add_child(npc_move)
        root.add_child(npc_sequence)
        root.add_child(DriveDistance(ego, 100))
        return root

    def _create_test_criteria(self):
        criteria = []
        ego = self.ego_vehicles[0]
        goal_loc = self._collision_location

        criteria.append(
            IntersectionCollisionLeftTurnBrakeCriterion(
                actor=ego,
                hazard_actor=self.other_actors[0],
            )
        )

        criteria.append(
            IntersectionCollisionLeftTurnResumeCriterion(
                actor=ego,
                goal_location=goal_loc,
                route_center_x=40,
                goal_dist_threshold=3.0,
                center_recover_threshold=2.0,
                min_resume_speed=1.0,
            )
        )

        criteria.append(
            MinTTCAutoCriterion(
                actor=ego,
                other_actors=self.other_actors,
                distance_threshold=40.0,
                forward_angle_deg=140.0,
                terminate_on_failure=False,
            )
        )
        return criteria

    def __del__(self):
        self.remove_all_actors()


try:
    from srunner.scenarios import route_scenario
    route_scenario.IntersectionCollisionLeftTurn = IntersectionCollisionLeftTurn
except ImportError:
    pass