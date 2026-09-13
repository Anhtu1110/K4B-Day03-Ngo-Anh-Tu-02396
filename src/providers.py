"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import re
from typing import Dict, Any, List
from dotenv import load_dotenv


# Đảm bảo output tiếng Việt hiển thị đúng trên Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


load_dotenv()


# ============================================================
# BASE PROVIDER
# ============================================================

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = ""
    ) -> Dict[str, Any]:
        raise NotImplementedError


# ============================================================
# MOCK OFFLINE PROVIDER
# ============================================================

class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""

    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(
        self,
        prompt: str,
        system_prompt: str = ""
    ) -> str:
        return (
            f"[Mock Chatbot Response]: Xin chào! "
            f"Tôi đã nhận được câu hỏi '{prompt}'. "
            f"(Chế độ Chatbot không có Tool tra cứu dữ liệu thời gian thực)."
        )

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = ""
    ) -> Dict[str, Any]:

        prompt_lower = prompt.lower()

        # =====================================================
        # 1. Trích xuất mã sinh viên từ câu hỏi
        # =====================================================

        student_match = re.search(
            r"\bSV\d+\b",
            prompt,
            re.IGNORECASE
        )

        student_id = (
            student_match.group(0).upper()
            if student_match
            else None
        )

        # =====================================================
        # 2. MULTI-STEP REACT
        #
        # Nếu context đã có Observation và người dùng yêu cầu
        # đặt lịch, Mock Agent sẽ lấy advisor từ Observation
        # rồi gọi schedule_appointment.
        # =====================================================
        # Multi-step reasoning:
# Tra cứu cố vấn trước, sau đó mới đặt lịch.
        if (
            student_id
            and "tra cứu" in prompt_lower
            and "cố vấn" in prompt_lower
            and "đặt lịch" in prompt_lower
            and "observation" not in prompt_lower
        ):
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {
                    "student_id": student_id
                },
                "thought": (
                    f"Tôi cần tra cứu thông tin của {student_id} "
                    f"để xác định cố vấn học tập trước khi đặt lịch."
                )
            }

        if (
            "đặt lịch" in prompt_lower
            and student_id
            and "observation" in prompt_lower
        ):

            advisor_match = re.search(
                r'"advisor"\s*:\s*"([^"]+)"',
                prompt
            )

            datetime_match = re.search(
                r"\b\d{1,2}:\d{2}\s+\d{1,2}/\d{1,2}/\d{4}\b",
                prompt
            )

            advisor_name = (
                advisor_match.group(1)
                if advisor_match
                else None
            )

            datetime_str = (
                datetime_match.group(0)
                if datetime_match
                else None
            )

            if advisor_name and datetime_str:

                return {
                    "type": "tool_call",
                    "tool_name": "schedule_appointment",
                    "arguments": {
                        "student_id": student_id,
                        "datetime_str": datetime_str,
                        "advisor_name": advisor_name
                    },
                    "thought": (
                        f"Đã tra cứu được cố vấn {advisor_name} "
                        f"cho sinh viên {student_id}. "
                        f"Tôi sẽ dùng thông tin này để đặt lịch."
                    )
                }

        # =====================================================
        # 3. ĐẶT LỊCH TRỰC TIẾP
        # =====================================================

        if "đặt lịch" in prompt_lower and student_id:

            datetime_match = re.search(
                r"\b\d{1,2}:\d{2}\s+\d{1,2}/\d{1,2}/\d{4}\b",
                prompt
            )

            datetime_str = (
                datetime_match.group(0)
                if datetime_match
                else "14:00 15/09/2026"
            )

            advisor_match = re.search(
                r"với\s+(.+?)(?:\s*\.$|$)",
                prompt,
                re.IGNORECASE
            )

            advisor_name = (
                advisor_match.group(1).strip()
                if advisor_match
                else "PGS.TS Nguyễn Văn A"
            )

            return {
                "type": "tool_call",
                "tool_name": "schedule_appointment",
                "arguments": {
                    "student_id": student_id,
                    "datetime_str": datetime_str,
                    "advisor_name": advisor_name
                },
                "thought": (
                    f"Người dùng yêu cầu đặt lịch hẹn tư vấn "
                    f"cho sinh viên {student_id}. "
                    f"Tôi sẽ gọi tool schedule_appointment."
                )
            }

        # =====================================================
        # 4. TRA CỨU HỌC VỤ
        # =====================================================

        if student_id and (
            "tra cứu" in prompt_lower
            or "học vụ" in prompt_lower
            or "cố vấn" in prompt_lower
        ):

            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {
                    "student_id": student_id
                },
                "thought": (
                    f"Người dùng muốn tra cứu thông tin học vụ "
                    f"của sinh viên {student_id}. "
                    f"Tôi sẽ gọi tool academic_query."
                )
            }

        # =====================================================
        # 5. CÂU HỎI CHUNG
        # =====================================================

        return {
            "type": "text",
            "content": (
                "[Mock Agent Response]: Xin chào! Quy chế học vụ "
                "VinUni yêu cầu sinh viên tích lũy tối thiểu 120 "
                "tín chỉ và duy trì GPA trên 2.0 để tốt nghiệp."
            ),
            "thought": (
                "Câu hỏi chung về quy chế học vụ, "
                "trả lời trực tiếp không cần gọi Tool."
            )
        }


# ============================================================
# GEMINI PROVIDER
# ============================================================

class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""

    def __init__(
        self,
        api_key: str = None,
        model: str = None
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = (
            model
            or os.getenv("LLM_MODEL")
            or "gemini-2.5-flash"
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str = ""
    ) -> str:

        if (
            not self.api_key
            or self.api_key == "your_gemini_api_key_here"
        ):
            return (
                "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY "
                "trong file .env! Đang sử dụng chế độ Mock."
            )

        try:
            from google import genai

            client = genai.Client(
                api_key=self.api_key
            )

            contents = (
                f"{system_prompt}\n\n{prompt}"
                if system_prompt
                else prompt
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )

            return response.text

        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = ""
    ) -> Dict[str, Any]:

        if (
            not self.api_key
            or self.api_key == "your_gemini_api_key_here"
        ):
            print(
                "ℹ️ [Gemini Provider]: "
                "Chưa tìm thấy GEMINI_API_KEY hợp lệ. "
                "Tự động chuyển sang Mock Offline."
            )

            return MockOfflineProvider().generate_with_tools(
                prompt,
                tools_schema,
                system_prompt
            )

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(
                api_key=self.api_key
            )

            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []

            for tool in tools_schema:

                if (
                    not tool.get("name")
                    or not tool.get("parameters")
                ):
                    continue

                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get(
                        "description",
                        ""
                    ),
                    "parameters": tool.get(
                        "parameters",
                        {}
                    )
                })

            config = types.GenerateContentConfig(
                system_instruction=(
                    system_prompt
                    if system_prompt
                    else None
                ),
                tools=(
                    [{
                        "function_declarations":
                        function_declarations
                    }]
                    if function_declarations
                    else None
                ),
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:

                call = response.function_calls[0]

                args = (
                    dict(call.args)
                    if hasattr(call, "args")
                    and call.args
                    else {}
                )

                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": (
                        f"Gemini quyết định gọi công cụ "
                        f"'{call.name}' với tham số: "
                        f"{json.dumps(args, ensure_ascii=False)}"
                    )
                }

            else:

                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": (
                        "Gemini phản hồi trực tiếp bằng văn bản "
                        "(không cần gọi công cụ)."
                    )
                }

        except Exception as e:

            print(
                f"⚠️ [Gemini API Warning]: "
                f"Không thể kết nối live API ({str(e)}). "
                f"Tự động fallback về Mock."
            )

            return MockOfflineProvider().generate_with_tools(
                prompt,
                tools_schema,
                system_prompt
            )


# ============================================================
# OPENAI PROVIDER
# ============================================================

class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""

    def __init__(
        self,
        api_key: str = None,
        model: str = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = (
            model
            or os.getenv("LLM_MODEL")
            or "gpt-4o-mini"
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str = ""
    ) -> str:

        if (
            not self.api_key
            or self.api_key == "your_openai_api_key_here"
        ):
            return (
                "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY "
                "trong file .env! Đang sử dụng chế độ Mock."
            )

        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=self.api_key
            )

            messages = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )

            return (
                response.choices[0].message.content
                or ""
            )

        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = ""
    ) -> Dict[str, Any]:

        if (
            not self.api_key
            or self.api_key == "your_openai_api_key_here"
        ):
            print(
                "ℹ️ [OpenAI Provider]: "
                "Chưa tìm thấy OPENAI_API_KEY hợp lệ. "
                "Tự động chuyển sang Mock Offline."
            )

            return MockOfflineProvider().generate_with_tools(
                prompt,
                tools_schema,
                system_prompt
            )

        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=self.api_key
            )

            tools = []

            for tool in tools_schema:

                if not tool.get("name"):
                    continue

                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get(
                            "description",
                            ""
                        ),
                        "parameters": tool.get(
                            "parameters",
                            {}
                        )
                    }
                })

            messages = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice=(
                    "auto"
                    if tools
                    else None
                )
            )

            msg = response.choices[0].message

            if msg.tool_calls:

                call = msg.tool_calls[0]

                args = (
                    json.loads(call.function.arguments)
                    if call.function.arguments
                    else {}
                )

                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": (
                        f"OpenAI quyết định gọi công cụ "
                        f"'{call.function.name}' với tham số: "
                        f"{json.dumps(args, ensure_ascii=False)}"
                    )
                }

            else:

                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": (
                        "OpenAI phản hồi trực tiếp bằng văn bản "
                        "(không cần gọi công cụ)."
                    )
                }

        except Exception as e:

            print(
                f"⚠️ [OpenAI API Warning]: "
                f"Không thể kết nối live API ({str(e)}). "
                f"Tự động fallback về Mock."
            )

            return MockOfflineProvider().generate_with_tools(
                prompt,
                tools_schema,
                system_prompt
            )


# ============================================================
# PROVIDER FACTORY
# ============================================================

def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""

    provider_type = os.getenv(
        "LLM_PROVIDER",
        "gemini"
    ).lower()

    # --------------------------------------------------------
    # Gemini
    # --------------------------------------------------------

    if provider_type == "gemini":

        key = os.getenv("GEMINI_API_KEY")

        if (
            key
            and key != "your_gemini_api_key_here"
        ):
            return GeminiProvider()

        else:
            return MockOfflineProvider()

    # --------------------------------------------------------
    # OpenAI
    # --------------------------------------------------------

    elif provider_type == "openai":

        key = os.getenv("OPENAI_API_KEY")

        if (
            key
            and key != "your_openai_api_key_here"
        ):
            return OpenAIProvider()

        else:
            return MockOfflineProvider()

    # --------------------------------------------------------
    # Mock
    # --------------------------------------------------------

    elif provider_type == "mock":

        return MockOfflineProvider()

    # --------------------------------------------------------
    # Unknown provider
    # --------------------------------------------------------

    else:

        return MockOfflineProvider()