def compute_gate(common_facts):
    if common_facts["collision"]:
        return 0.0
    return 1.0


def compute_penalty(common_facts):
    penalty = 1.0

    min_ttc = common_facts.get("min_ttc")
    if min_ttc is not None:
        if min_ttc >= 2.0:
            penalty *= 1.00
        elif min_ttc >= 1.5:
            penalty *= 0.95
        elif min_ttc >= 1.0:
            penalty *= 0.85
        elif min_ttc >= 0.5:
            penalty *= 0.65
        else:
            penalty *= 0.0

    if common_facts["outside_route"]:
        penalty *= 0.9

    return penalty

# 场景特定分数计算

# 文件路径: /home/cpz/文档/Bench2Drive/leaderboard/leaderboard/utils/facts_to_score.py
# 在文件末尾添加以下函数

def score_ebike_pedestrian_cross(common_facts, private_facts):
    """
    EbikeAndPedestrianCross 场景的评分函数
    
    评分标准：
    - 识别电瓶车并减速: 25分
    - 识别行人并刹车: 50分
    - 离开风险区并恢复通行: 25分
    """
    base_score = 0.0

    # BaseScore: 根据私有事实计算
    if private_facts["ebike_decelerate"]:
        base_score += 25.0
    if private_facts["pedestrian_stop"]:
        base_score += 50.0
    if private_facts["resume_route"]:
        base_score += 25.0

    # Gate: 发生碰撞则分数归零
    gate = 1.0
    if common_facts.get("collision", False):
        gate = 0.0

    # Penalty: 基于最小TTC和越界
    penalty = 1.0
    min_ttc = common_facts.get("min_ttc")
    if min_ttc is not None:
        if min_ttc >= 2.0:
            penalty *= 1.00
        elif min_ttc >= 1.5:
            penalty *= 0.95
        elif min_ttc >= 1.0:
            penalty *= 0.85
        elif min_ttc >= 0.5:
            penalty *= 0.65
        else:
            penalty *= 0.0

    if common_facts.get("outside_route", False):
        penalty *= 0.9

    final_score = base_score * gate * penalty

    return {
        "base_score": base_score,
        "gate": gate,
        "penalty": penalty,
        "final_score": final_score,
        "breakdown": {
            "ebike_decelerate": private_facts["ebike_decelerate"],
            "pedestrian_stop": private_facts["pedestrian_stop"],
            "resume_route": private_facts["resume_route"],
            "collision": common_facts.get("collision", False),
            "min_ttc": min_ttc
        }
    }

def score_reverse_vehicle(common_facts, private_facts):
    """反向车辆场景评分（占位符）"""
    return {
        "base_score": 0,
        "gate": 1.0,
        "penalty": 1.0,
        "final_score": 0,
    }
