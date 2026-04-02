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

        elif name == "MinTTCriterion":
            # 你后面如果自己写一个最小TTC criterion，就可以从 actual_value 里拿
            common_facts["min_ttc"] = criterion.actual_value

    return common_facts


# 文件路径: /home/cpz/文档/Bench2Drive/leaderboard/leaderboard/utils/facts_creator.py
# 在文件末尾添加以下函数

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

def extract_private_facts_reverse_vehicle(criteria_list):
    """反向车辆场景的私有事实提取（占位符）"""
    facts = {
        "brake_response": False,
        "safe_bypass": False,
        "resume_route": False,
    }
    return facts

