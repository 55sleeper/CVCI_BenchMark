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
            # 这里只是示意，具体要看你怎么定义“outside_route”
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

def extract_private_facts_roundabout_merge_conflict(criteria_list):
    """
    大转盘极端交互场景的私有事实提取
    """
    facts = {
        "decelerate_response": False,
        "safe_merge": False,
        "yield_convoy": False,
    }

    for criterion in criteria_list:
        if criterion.name == "RoundaboutDecelerateCriterion":
            facts["decelerate_response"] = (criterion.test_status == "SUCCESS")

        elif criterion.name == "RoundaboutSafeMergeCriterion":
            facts["safe_merge"] = (criterion.test_status == "SUCCESS")

        elif criterion.name == "RoundaboutYieldConvoyCriterion":
            facts["yield_convoy"] = (criterion.test_status == "SUCCESS")

    return facts


def extract_private_facts_broken_down_vehicle(criteria_list):
    facts = {
        "brake_response": False,
        "safe_bypass": False,
        "resume_route": False,
    }

    for criterion in criteria_list:
        if criterion.name == "BrokenDownVehicleBrakeCriterion":
            facts["brake_response"] = (criterion.test_status == "SUCCESS")

        elif criterion.name == "BrokenDownVehicleBypassCriterion":
            facts["safe_bypass"] = (criterion.test_status == "SUCCESS")

        elif criterion.name == "BrokenDownVehicleResumeCriterion":
            facts["resume_route"] = (criterion.test_status == "SUCCESS")

    return facts


def extract_hht_private_facts_reverse_vehicle(criteria_list):
    facts = {
        "brake_response": False,
        "safe_bypass": False,
        "resume_route": False,
    }

    for criterion in criteria_list:
        if criterion.name == "IntersectionCollisionLeftTurnBrakeCriterion":
            facts["brake_response"] = (criterion.test_status == "SUCCESS")

        elif criterion.name == "IntersectionCollisionLeftTurnResumeCriterion":
            facts["resume_route"] = (criterion.test_status == "SUCCESS")

    return facts

def extract_private_facts_ebike_pedestrian_cross(criteria_list):
    """
    提取 EbikeAndPedestrianCross 场景的私有事实
    """
    facts = {
        "ebike_decelerate": False,      # 识别电瓶车并减速
        "pedestrian_stop": False,       # 识别行人并刹车
        "resume_route": False,          # 离开风险区并恢复通行
    }

    for criterion in criteria_list:
        if criterion.name == "EbikeDetectionAndDecelerateCriterion":
            facts["ebike_decelerate"] = (criterion.test_status == "SUCCESS")

        elif criterion.name == "PedestrianDetectionAndStopCriterion":
            facts["pedestrian_stop"] = (criterion.test_status == "SUCCESS")

        elif criterion.name == "ResumeAfterPedestrianCriterion":
            facts["resume_route"] = (criterion.test_status == "SUCCESS")

    return facts


    """
    Extract relevant facts from the LaneClosureWithTruck scenario.

    Args:
        scenario: The scenario object containing criteria

    Returns:
        dict: A dictionary containing the extracted facts
    """
    facts = {
        'deceleration_detected': False,
        'speed_reduction': 0.0,
        'collision_count': 0,
        'route_passed': False,
        'distance_traveled': 0.0,
        'criteria_status': {}
    }

    if not scenario:
        return facts

    # Get all criteria from the scenario
    criteria_list = scenario.get_criteria()

    for criterion in criteria_list:
        criterion_name = criterion.name
        facts['criteria_status'][criterion_name] = criterion.test_status

        # Extract deceleration facts
        if criterion_name == "DecelerationForConstructionTest":
            if criterion.test_status == "SUCCESS":
                facts['deceleration_detected'] = True
            facts['speed_reduction'] = criterion.actual_value

        # Extract collision facts
        elif criterion_name == "CollisionTest":
            facts['collision_count'] = criterion.actual_value

        # Extract route completion facts
        elif criterion_name == "RoutePassCompletionTest":
            if criterion.test_status == "SUCCESS":
                facts['route_passed'] = True
            facts['distance_traveled'] = criterion.actual_value

    return facts