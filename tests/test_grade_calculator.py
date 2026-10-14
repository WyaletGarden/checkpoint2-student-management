import pytest
from app.utils.grade_calculator import classify_student_score

# 1. Test các trường hợp xếp loại thành công với nhiều mức điểm khác nhau
@pytest.mark.parametrize(
    "score, expected_grade",
    [
        (9.5, "Giỏi"),
        (8.5, "Giỏi"),  # Biên dưới của Giỏi
        (8.4, "Khá"),
        (7.0, "Khá"),   # Biên dưới của Khá
        (6.9, "Trung bình"),
        (5.0, "Trung bình"), # Biên dưới của Trung bình
        (4.9, "Yếu"),
        (0.0, "Yếu"),   # Biên dưới cùng
    ]
)
def test_classify_student_score_success(score, expected_grade):
    result = classify_student_score(score)
    assert result == expected_grade


# 2. Test các trường hợp đầu vào không hợp lệ (phải bắn ra ngoại lệ ValueError)
@pytest.mark.parametrize(
    "invalid_score",
    [-0.5, 10.1, 15.0, -10.0]
)
def test_classify_student_score_invalid_input(invalid_score):
    # Dùng pytest.raises để kiểm tra xem hàm có bắn đúng lỗi ValueError không
    with pytest.raises(ValueError, match="Điểm số phải nằm trong khoảng từ 0.0 đến 10.0"):
        classify_student_score(invalid_score)