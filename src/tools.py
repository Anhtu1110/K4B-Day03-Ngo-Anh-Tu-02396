
import json
from typing import Dict, Any


TOOLS_SCHEMA = [

    # Tool 1: Tra cứu thông tin học vụ
    {
        "name": "academic_query",
        "description": "Tra cứu hồ sơ và thông tin học vụ của sinh viên VinUni bằng mã sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu (ví dụ: 'SV2026001')"
                }
            },
            "required": ["student_id"]
        }
    },

    # Tool 2: Đặt lịch tư vấn học vụ
    {
        "name": "schedule_appointment",
        "description": "Đặt lịch hẹn tư vấn học vụ với Cố vấn học tập VinUni.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần đặt lịch (ví dụ: 'SV2026001')"
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian hẹn (ví dụ: '14:00 15/09/2026')"
                },
                "advisor_name": {
                    "type": "string",
                    "description": "Tên cố vấn học tập"
                }
            },
            "required": [
                "student_id",
                "datetime_str",
                "advisor_name"
            ]
        }
    }
]


MOCK_DATABASE = {
    "SV2026001": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
    },
    "SV2026002": {
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "gpa": 3.60,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B"
    }
}


def execute_academic_query(student_id: str) -> str:
    student = MOCK_DATABASE.get(student_id.strip().upper())

    if student:
        return json.dumps({
            "status": "SUCCESS",
            "student_id": student_id,
            "data": student
        }, ensure_ascii=False)

    return json.dumps({
        "status": "NOT_FOUND",
        "message": f"Không tìm thấy dữ liệu sinh viên có mã '{student_id}'"
    }, ensure_ascii=False)


def execute_schedule_appointment(
    student_id: str,
    datetime_str: str,
    advisor_name: str
) -> str:
    return json.dumps({
        "status": "SUCCESS",
        "booking_id": f"BK-{student_id}-99",
        "student_id": student_id,
        "datetime": datetime_str,
        "advisor": advisor_name,
        "message": (
            f"Đặt lịch thành công cho sinh viên {student_id} "
            f"với {advisor_name} vào lúc {datetime_str}."
        )
    }, ensure_ascii=False)


TOOL_ROUTER = {
    "academic_query": execute_academic_query,
    "schedule_appointment": execute_schedule_appointment
}


def dispatch_tool_call(
    tool_name: str,
    arguments: Dict[str, Any]
) -> str:
    """Điều phối yêu cầu gọi Tool tới đúng hàm thực thi."""

    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)

        except Exception as e:
            return json.dumps({
                "status": "EXECUTION_ERROR",
                "error": str(e)
            }, ensure_ascii=False)

    return json.dumps({
        "status": "UNKNOWN_TOOL",
        "error": f"Tool '{tool_name}' không tồn tại!"
    }, ensure_ascii=False)