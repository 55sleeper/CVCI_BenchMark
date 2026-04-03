def extract_common_facts(criteria_list):
    common_facts = {
        "collision": False,
        "min_ttc": None,
        "outside_route": False,
        "running_red_light": False,
        "running_stop": False,
        "agent_blocked": False,
        "route_completed": False,
    }
    for criterion in criteria_list:
        name = criterion.name
        if name == "CollisionTest":
            common_facts["collision"] = (criterion.test_status == "FAILURE" or len(criterion.events) > 0)

        elif name == "OutsideRouteLanesTest":
            common_facts["outside_route"] = (criterion.test_status == "FAILURE")

        elif name == "RunningRedLightTest":
            common_facts["running_red_light"] = (criterion.test_status == "FAILURE")

        elif name == "RunningStopTest":
            common_facts["running_stop"] = (criterion.test_status == "FAILURE")

        elif name == "AgentBlockedTest":
            common_facts["agent_blocked"] = (criterion.test_status == "FAILURE")

        elif name == "RouteCompletionTest":
            common_facts["route_completed"] = (criterion.test_status == "SUCCESS")

        elif name == "MinTTCAutoCriterion":
            print(criterion.actual_value)
            common_facts["min_ttc"] = float(criterion.actual_value)

    return common_facts

# missing car_private_facats extracts

# High speed temporary construction_private_facats extracts

# High-speed reckless lane cutting_private_facats extracts

# Highway accident vehicle_private_facats extracts
def extract_private_facts_high_speed_accident(criteria_list):
    """提取高速深夜事故场景的私有事实"""
    facts = {
        "brake_response": False,    # 识别事故车并减速
        "safe_bypass": False,       # 安全绕行
        "resume_route": False,      # 成功通过事故区域后恢复行驶
    }
    for criterion in criteria_list:
        if criterion.name == "HighSpeedBrakeCriterion":
            facts["brake_response"] = (criterion.test_status == "SUCCESS")
        elif criterion.name == "HighSpeedBypassCriterion":
            facts["safe_bypass"] = (criterion.test_status == "SUCCESS")
        elif criterion.name == "HighSpeedResumeCriterion":
            facts["resume_route"] = (criterion.test_status == "SUCCESS")
    return facts
# Trucks encountered during construction_private_facats extracts
def extract_lane_closure_facts(scenario, parent_scenario=None):
    facts = {
        'deceleration_detected': False,
        'speed_reduction': 0.0,
        'collision_count': 0,
        'route_passed': False,
        'distance_traveled': 0.0,
        'min_ttc': None,
        'criteria_status': {}
    }

    if not scenario:
        return facts

    criteria_list = scenario.get_criteria()

    if parent_scenario and hasattr(parent_scenario, 'get_criteria'):
        parent_criteria_list = parent_scenario.get_criteria()
        print(f"[DEBUG Facts Extract] Parent scenario has {len(parent_criteria_list)} criteria", flush=True)
        criteria_list = list(criteria_list) + list(parent_criteria_list)

    for criterion in criteria_list:
        criterion_name = criterion.name
        facts['criteria_status'][criterion_name] = criterion.test_status

        if criterion_name == "DecelerationForConstructionTest":
            if criterion.test_status == "SUCCESS":
                facts['deceleration_detected'] = True
            facts['speed_reduction'] = criterion.actual_value
            print(f"[DEBUG Facts Extract] DecelerationForConstructionTest: status={criterion.test_status}, actual_value={criterion.actual_value}", flush=True)

        elif criterion_name == "CollisionTest":
            facts['collision_count'] = criterion.actual_value
            print(f"[DEBUG Facts Extract] CollisionTest: status={criterion.test_status}, actual_value={criterion.actual_value}, id={id(criterion)}", flush=True)

        elif criterion_name == "RoutePassCompletionTest":
            if criterion.test_status == "SUCCESS":
                facts['route_passed'] = True
            facts['distance_traveled'] = criterion.actual_value
            print(f"[DEBUG Facts Extract] RoutePassCompletionTest: status={criterion.test_status}, actual_value={criterion.actual_value}", flush=True)

        elif "TTC" in criterion_name.upper():
            facts['min_ttc'] = criterion.actual_value
            print(f"[DEBUG Facts Extract] {criterion_name}: actual_value={criterion.actual_value}", flush=True)

    return facts
# Drive into the roundabout_private_facats extracts

# Four students crossing the road_private_facats extracts
def extract_private_facts_ghost_probe(criteria_root):
    """提取鬼探头场景的私有事实"""
    facts = {
        "scooter_decelerate": False,    # 识别到电动车并成功减速
        "pedestrian_stop": False,       # 识别到行人并成功停车
        "pedestrian_resume": False,     # 待行人离开后恢复行驶
    }

    nodes = criteria_root.iterate() if hasattr(criteria_root, 'iterate') else criteria_root

    for criterion in nodes:
        if hasattr(criterion, 'name'):
            if criterion.name == "ScooterDecelerateCriterion":
                facts["scooter_decelerate"] = (criterion.test_status == "SUCCESS")
            elif criterion.name == "PedestrianStopCriterion":
                facts["pedestrian_stop"] = (criterion.test_status == "SUCCESS")
            elif criterion.name == "PedestrianResumeCriterion":
                facts["pedestrian_resume"] = (criterion.test_status == "SUCCESS")

    return facts
# avoid a disabled vehicle_private_facats extracts

# Slanted motor and children_private_facats extracts

# reverse vehicle_private_facats extracts
def extract_private_facts_reverse_vehicle(criteria_list):
    facts = {
        "brake_response": False,
        "safe_bypass": False,
        "resume_route": False,
    }

    for criterion in criteria_list:
        if criterion.name == "ReverseVehicleBrakeCriterion":
            facts["brake_response"] = (criterion.brake_status == "SUCCESS")

        elif criterion.name == "ReverseVehicleBypassCriterion":
            facts["safe_bypass"] = (criterion.bypass_status == "SUCCESS")

        elif criterion.name == "ReverseVehicleResumeCriterion":
            facts["resume_route"] = (criterion.resume_status == "SUCCESS")

    return facts

# crazy motor_private_facats extracts

# Blind spot hidden car_private_facats extracts
