def classify_student_score(score: float) -> str:
    """
    Xếp loại học lực dựa trên điểm số (thang điểm 10).
    - Giỏi: >= 8.5
    - Khá: >= 7.0 và < 8.5
    - Trung bình: >= 5.0 và < 7.0
    - Yếu: < 5.0
    """
    if score < 0.0 or score > 10.0:
        raise ValueError("Điểm số phải nằm trong khoảng từ 0.0 đến 10.0")
    
    if score >= 8.5:
        return "Giỏi"
    elif score >= 7.0:
        return "Khá"
    elif score >= 5.0:
        return "Trung bình"
    else:
        return "Yếu"