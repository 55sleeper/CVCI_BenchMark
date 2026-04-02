#!/usr/bin/env python

import py_trees
import carla

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenarios.basic_scenario import BasicScenario
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import (ActorTransformSetter,
                                                                     WaypointFollower,
                                                                     AccelerateToVelocity)
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import InTriggerDistanceToLocation
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_criteria import (RoundaboutDecelerateCriterion, 
                                                                    RoundaboutSafeMergeCriterion, 
                                                                    RoundaboutYieldConvoyCriterion)

class RoundaboutMergeConflict(BasicScenario):

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=60):
        self.timeout = timeout
        self._map = CarlaDataProvider.get_map()
        
        # 1. 触发点硬编码 (对应 XML 中的 trigger_point)
        self._trigger_location = carla.Location(x=2.6, y=32.9, z=0.0)

        self._init_speed = float(
            config.other_parameters.get("init_speed", {}).get("value", 11.0)
        )
        
        # 2. 基础参数硬编码
        self._start_distance = 5.0
        self._adversary_speed = 5.0
        self._adversary_throttle = 0.6
        self._chedui_speed = 5.0
        self._num_convoy_vehicles = 6  # 车队车辆数量

        # 3. 【原车】路点硬编码
        self._adversary_waypoints = [
            carla.Location(x=-1.1, y=23.6, z=0.5),
            carla.Location(x=1.8, y=23.5, z=0.5),
            carla.Location(x=6.4, y=22.6, z=0.5),
            carla.Location(x=11.6, y=20.6, z=0.5),
            carla.Location(x=16.6, y=15.0, z=0.5),
            carla.Location(x=19.9, y=11.3, z=0.5),
            carla.Location(x=22.5, y=3.0, z=0.5),
            carla.Location(x=21.1, y=-8.6, z=0.5),
        ]

        # 4. 【车队】路径点硬编码 (内圈)
        self._convoy_waypoints = [
            # carla.Location(x=7.2, y=18.1, z=0.5), 
            # carla.Location(x=14.7, y=12.6, z=0.5),
            # carla.Location(x=18.8, y=5.7, z=0.5),
            # carla.Location(x=5.0, y=18.0, z=0.5),  # 向外上方扩展
            carla.Location(x=15.0, y=15.0, z=0.5), # 中点向外偏移
            carla.Location(x=20.0, y=7.0, z=0.5),  # 向外下方扩展
            carla.Location(x=17.7, y=-3.5, z=0.5),
            carla.Location(x=14.4, y=-14.8, z=0.5),
            carla.Location(x=6.7, y=-35.4, z=0.5),
            carla.Location(x=16.7, y=-70.4, z=0.5),
        ]

        # 5. 【车队】初始出生点
        self._convoy_start_transforms = [
            carla.Transform(carla.Location(x=0.6, y=21.0, z=0.5), carla.Rotation(yaw=0.0)),   # 0号车
            # carla.Transform(carla.Location(x=-1.5, y=19.5, z=0.5), carla.Rotation(yaw=20.0)),  # 1号车
            carla.Transform(carla.Location(x=-12.0, y=15.8, z=0.5), carla.Rotation(yaw=40.0)), # 2号车
            carla.Transform(carla.Location(x=-18.6, y=9.6, z=0.5), carla.Rotation(yaw=60.0)),  # 3号车
            carla.Transform(carla.Location(x=-20.3, y=-0.4, z=0.5), carla.Rotation(yaw=90.0)), # 4号车
            carla.Transform(carla.Location(x=-16.8, y=-10.7, z=0.5), carla.Rotation(yaw=110.0)),# 5号车
            carla.Transform(carla.Location(x=-11.3, y=-15.8, z=0.5), carla.Rotation(yaw=120.0)),# 6号车
        ]
#         self._convoy_start_transforms = [
#             # 0号车：稍微向右、向上移
#             carla.Transform(carla.Location(x=3.5, y=22.0, z=0.5), carla.Rotation(yaw=0.0)),   
#             # 1号车：增加偏左和向上的幅度
#             carla.Transform(carla.Location(x=-2.5, y=22.5, z=0.5), carla.Rotation(yaw=20.0)),  
#             # 2号车：向左上外扩
#             carla.Transform(carla.Location(x=-15.0, y=18.5, z=0.5), carla.Rotation(yaw=40.0)), 
#             # 3号车：圆弧最外侧点，显著增加 x 的负值
#             carla.Transform(carla.Location(x=-24.0, y=11.0, z=0.5), carla.Rotation(yaw=60.0)),  
#             # 4号车：中间转弯处，向左推移
#             carla.Transform(carla.Location(x=-26.5, y=-0.5, z=0.5), carla.Rotation(yaw=90.0)), 
#             # 5号车：左下方外扩
#             carla.Transform(carla.Location(x=-22.0, y=-14.0, z=0.5), carla.Rotation(yaw=110.0)),
#             # 6号车：终点位置下移并左移
#             carla.Transform(carla.Location(x=-15.0, y=-20.5, z=0.5), carla.Rotation(yaw=120.0)),
# ]

        # --- 核心修改：提前为每辆车生成专属路线并可视化 ---
        self.convoy_plans = []
        
        # 准备7种不同的颜色用于画线 (红, 绿, 蓝, 黄, 紫, 青, 橙)
        debug_colors = [
            carla.Color(255, 0, 0),    
            carla.Color(0, 255, 0),    
            carla.Color(0, 0, 255),    
            carla.Color(255, 255, 0),  
            carla.Color(255, 0, 255),  
            carla.Color(0, 255, 255),  
            carla.Color(255, 128, 0)   
        ]

        for idx in range(self._num_convoy_vehicles):
            individual_plan = []
            
            # 将前方车辆的出生点依次加入
            for prev_idx in range(idx - 1, -1, -1):
                individual_plan.append(self._convoy_start_transforms[prev_idx].location)
                
            # 最后拼接共用的内部环岛轨迹
            individual_plan.extend(self._convoy_waypoints)
            self.convoy_plans.append(individual_plan)

            # # 绘制该车的 debug 路线
            # color = debug_colors[idx % len(debug_colors)]
            # start_loc = self._convoy_start_transforms[idx].location
            
            # for i, loc in enumerate(individual_plan):
            #     # 把 Z 轴抬高一点点，防止被地面遮挡
            #     draw_loc = loc + carla.Location(z=1.0)
                
            #     # 画点
            #     world.debug.draw_point(draw_loc, size=0.15, color=color, life_time=100.0)
                
            #     # 画线
            #     if i == 0:
            #         prev_loc = start_loc + carla.Location(z=1.0)
            #     else:
            #         prev_loc = individual_plan[i-1] + carla.Location(z=1.0)
                    
            #     world.debug.draw_line(prev_loc, draw_loc, thickness=0.1, color=color, life_time=100.0)

        super(RoundaboutMergeConflict, self).__init__("RoundaboutMergeConflict",
                                                      ego_vehicles,
                                                      config,
                                                      world,
                                                      debug_mode,
                                                      criteria_enable=criteria_enable)
        
        # # 绘制原车的 debug 路线 (白色)
        # for i, loc in enumerate(self._adversary_waypoints):
        #     world.debug.draw_point(loc + carla.Location(z=1.0), size=0.15, color=carla.Color(255,255,255), life_time=100.0)
        #     if i > 0:
        #         world.debug.draw_line(self._adversary_waypoints[i-1] + carla.Location(z=1.0), 
        #                             loc + carla.Location(z=1.0), 
        #                             thickness=0.1, color=carla.Color(255,255,255), life_time=100.0)

    def _initialize_actors(self, config):
        # 1. 障碍车初始化
        obstacle_transform = carla.Transform(
            carla.Location(x=3, y=32.0, z=0.5), 
            carla.Rotation(pitch=0.0, yaw=270.0, roll=0.0)
        )
        obstacle_actor = CarlaDataProvider.request_new_actor('vehicle.toyota.prius', obstacle_transform)
        if obstacle_actor:
            obstacle_actor.set_simulate_physics(True)
            self.other_actors.append(obstacle_actor) 

        # 2. 原来的动态来车初始化
        adversary_transform = carla.Transform(
            carla.Location(x=-7.9, y=22.7, z=0.5),
            carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0)
        )
        adversary_actor = CarlaDataProvider.request_new_actor('vehicle.lincoln.mkz_2017', adversary_transform)
        if adversary_actor:
            adversary_actor.set_simulate_physics(True)
            self.other_actors.append(adversary_actor) 

        # 3. 新增的动态车队初始化 (7辆车)
        self.convoy_actors = [] 
        for i in range(self._num_convoy_vehicles):
            spawn_transform = self._convoy_start_transforms[i]
            actor = CarlaDataProvider.request_new_actor('vehicle.lincoln.mkz_2017', spawn_transform)
            if actor:
                actor.set_simulate_physics(True)
                self.other_actors.append(actor)
                self.convoy_actors.append(actor)

        # 为自车设置初始速度
        if self.ego_vehicles:
            ego = self.ego_vehicles[0]
            # 计算速度矢量（需要根据自车的朝向）
            forward_vector = ego.get_transform().get_forward_vector()
            velocity_ms = self._init_speed
            ego.set_target_velocity(carla.Vector3D(
                x=forward_vector.x * velocity_ms,
                y=forward_vector.y * velocity_ms,
                z=forward_vector.z * velocity_ms
            ))

    def _create_behavior(self):
        # ---------------- 1. 原车行为逻辑 ----------------
        original_adversary = self.other_actors[1]
        
        original_sequence = py_trees.composites.Sequence("OriginalAdversaryBehavior")
        trigger_1 = InTriggerDistanceToLocation(
            self.ego_vehicles[0], self._trigger_location, self._start_distance, name="Wait for ego (Original)")
        keep_driving_1 = WaypointFollower(
            original_adversary, target_speed=self._adversary_speed, plan=self._adversary_waypoints, avoid_collision=True, name="FollowWaypoints (Original)")
        original_sequence.add_children([trigger_1, keep_driving_1])


        # ---------------- 2. 车队行为逻辑 ----------------
        convoy_sequence = py_trees.composites.Sequence("ConvoyBehavior")
        trigger_2 = InTriggerDistanceToLocation(
            self.ego_vehicles[0], self._trigger_location, self._start_distance, name="Wait for ego (Convoy)")
        
        convoy_parallel = py_trees.composites.Parallel("ConvoyParallelBehavior", policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL)
        for idx, actor in enumerate(self.convoy_actors):
            # 直接使用在 __init__ 中生成好的路线
            keep_driving_convoy = WaypointFollower(
                actor, 
                target_speed=self._chedui_speed, 
                plan=self.convoy_plans[idx], 
                avoid_collision=False, 
                name=f"FollowWaypoints_Vehicle_{idx}"
            )
            convoy_parallel.add_child(keep_driving_convoy)
            
        convoy_sequence.add_children([trigger_2, convoy_parallel])

        # ---------------- 3. 总控制器 ----------------
        root = py_trees.composites.Parallel("AllAdversariesRoot", policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL)
        root.add_children([original_sequence, convoy_sequence])

        return root

    def _create_test_criteria(self):
        criteria = [CollisionTest(self.ego_vehicles[0])]
        
        ego = self.ego_vehicles[0]
        adversary = self.other_actors[1] 

        # 条件1 & 2 保持原样...
        criteria.append(RoundaboutDecelerateCriterion(actor=ego))
        criteria.append(RoundaboutSafeMergeCriterion(actor=ego, adversary=adversary))

        # 确保传入了 actor=self.ego_vehicles[0]
        # 且传入了 convoy_actors=self.convoy_actors
        yield_criterion = RoundaboutYieldConvoyCriterion(
            actor=self.ego_vehicles[0], 
            convoy_actors=self.convoy_actors
        )
        criteria.append(yield_criterion)
        return criteria

    # def _create_test_criteria(self):
    #     return [CollisionTest(self.ego_vehicles[0])]


    def __del__(self):
        self.remove_all_actors()