
"""
CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")

    if not os.path.exists(config_path):
        example_path = os.path.join(
            base_dir,
            "config",
            "test_cases.example.json"
        )

        if os.path.exists(example_path):
            print(
                "[CONFIG NOTICE]: Chưa thấy file "
                "'config/test_cases.json'. Đang dùng mẫu "
                "'config/test_cases.example.json'."
            )
            print(
                "Hãy chạy: copy config/test_cases.example.json "
                "config/test_cases.json và viết test cases theo đề tài của bạn!\n"
            )
            config_path = example_path
        else:
            config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""

    base_dir = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )

    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)

    trace_path = os.path.join(
        docs_dir,
        "trace_waterfall.json"
    )

    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(
            trace_data,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"[OBSERVABILITY]: Đã lưu {len(trace_data)} "
        f"sự kiện Waterfall Trace tại '{trace_path}'!"
    )


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""

    print(
        f"\n[CHATBOT BASELINE] Câu hỏi: {user_query}"
    )

    response = provider.generate(
        user_query,
        system_prompt=CHATBOT_BASELINE_PROMPT
    )

    print(
        f"Chatbot phản hồi:\n{response}"
    )


def run_react_agent(
    user_query: str,
    provider,
    mcp_server: MCPAcademicServer
) -> list:
    """
    [REACT AGENT LOOP]

    Thực thi vòng lặp:

        Thought
           ↓
        Action
           ↓
        Observation
           ↓
        Thought
           ↓
        ...

    Agent chỉ kết thúc khi:
    - LLM trả về Final Answer
    - Hoặc đạt MAX_ITERATIONS
    """

    print(
        f"\n[REACT AGENT] Câu hỏi: {user_query}"
    )

    step = 0
    trace_logs = []

    tools_list = mcp_server.list_tools()

    # Context ban đầu chỉ chứa câu hỏi của user.
    # Sau mỗi Tool Execution, Observation sẽ được
    # đưa trở lại LLM để quyết định bước tiếp theo.
    conversation_context = user_query

    while step < MAX_ITERATIONS:

        step += 1

        step_start_time = time.time()

        print(
            f"\n--- Vòng lặp ReAct Loop "
            f"(Step {step}/{MAX_ITERATIONS}) ---"
        )

        # =========================================================
        # 1. THOUGHT / DECISION
        # =========================================================

        llm_response = provider.generate_with_tools(
            conversation_context,
            tools_list,
            system_prompt=REACT_AGENT_SYSTEM_PROMPT
        )

        latency_ms = round(
            (time.time() - step_start_time) * 1000,
            2
        )

        thought = llm_response.get(
            "thought",
            "Đang suy luận..."
        )

        print(
            f"[Thought]: {thought}"
        )

        # =========================================================
        # 2. FINAL ANSWER
        # =========================================================

        if llm_response.get("type") == "text":

            final_content = llm_response.get(
                "content",
                ""
            )

            print(
                f"[Final Answer]: {final_content}"
            )

            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_content,
                "latency_ms": latency_ms
            })

            break

        # =========================================================
        # 3. TOOL CALL / ACTION
        # =========================================================

        elif llm_response.get("type") == "tool_call":

            tool_name = llm_response.get(
                "tool_name"
            )

            arguments = llm_response.get(
                "arguments",
                {}
            )

            print(
                f"[Action Proposed]: "
                f"{tool_name}({arguments})"
            )

            # =====================================================
            # Execute Tool through MCP Server
            # =====================================================

            tool_start_time = time.time()

            mcp_result = mcp_server.call_tool(
                tool_name,
                arguments
            )

            tool_latency_ms = round(
                (time.time() - tool_start_time) * 1000,
                2
            )

            obs_data = mcp_result.get(
                "result",
                {}
            )

            # =====================================================
            # Observation
            # =====================================================

            if not obs_data:

                print(
                    "[Observation từ MCP Server]: {}"
                )

                print(
                    "[CHÚ Ý]: MCP Server trả về kết quả rỗng!"
                )

                obs_data = {
                    "status": "EMPTY_RESULT",
                    "message": (
                        "MCP Server không trả về dữ liệu."
                    )
                }

            obs_str = json.dumps(
                obs_data,
                ensure_ascii=False
            )

            print(
                f"[Observation từ MCP Server]: "
                f"{obs_str}"
            )

            # =====================================================
            # Trace Log
            # =====================================================

            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": (
                    latency_ms + tool_latency_ms
                ),
                "details": {
                    "llm_latency_ms": latency_ms,
                    "tool_latency_ms": tool_latency_ms,
                    "status": obs_data.get(
                        "status",
                        "UNKNOWN"
                    )
                }
            })

            # =====================================================
            # IMPORTANT:
            #
            # KHÔNG FINALIZE Ở ĐÂY.
            #
            # Observation phải được đưa lại cho Agent.
            # Agent sẽ quyết định:
            #
            # Step 1:
            # academic_query
            #
            # Observation:
            # advisor = TS. Lê Thị B
            #
            # Step 2:
            # schedule_appointment
            #
            # Observation:
            # SUCCESS
            #
            # Step 3:
            # Final Answer
            # =====================================================

            conversation_context = f"""
User request:
{user_query}

Previous Agent Thought:
{thought}

Tool executed:
{tool_name}

Tool arguments:
{json.dumps(arguments, ensure_ascii=False)}

Observation from MCP Server:
{obs_str}

Continue solving the ORIGINAL user request.

Use the observation above as factual information.

If another tool is required to complete the user's request,
call the appropriate tool.

If the user's request is now fully completed,
return a concise final answer.

Do not ignore the original user request.
"""

            continue

        # =========================================================
        # 4. INVALID LLM RESPONSE
        # =========================================================

        else:

            final_answer = (
                "Agent nhận được phản hồi "
                "không hợp lệ từ LLM Provider."
            )

            print(
                f"[Agent Error]: {final_answer}"
            )

            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "ERROR",
                "thought": thought,
                "output": final_answer,
                "latency_ms": latency_ms,
                "details": {
                    "reason": "Invalid LLM response"
                }
            })

            break

    # =============================================================
    # MAX ITERATIONS
    # =============================================================

    if step >= MAX_ITERATIONS:

        print(
            "[ReAct]: Đã đạt giới hạn số vòng lặp."
        )

        # Nếu loop kết thúc vì MAX_ITERATIONS,
        # ghi thêm event để trace dễ kiểm tra.
        trace_logs.append({
            "step": step,
            "query": user_query,
            "action_type": "MAX_ITERATIONS",
            "thought": (
                "Agent đạt giới hạn số vòng lặp "
                "mà chưa hoàn tất."
            ),
            "output": "",
            "latency_ms": 0,
            "details": {
                "max_iterations": MAX_ITERATIONS
            }
        })

    return trace_logs


if __name__ == "__main__":

    print(
        "=========================================================="
    )
    print(
        "VINUNI AI COURSE - DAY 03 LAB: CHATBOT VS REACT AGENT"
    )
    print(
        "=========================================================="
    )

    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()

    print(
        f"LLM Provider: "
        f"{provider.__class__.__name__}"
    )

    print(
        f"MCP Server: "
        f"{mcp_server.server_name}\n"
    )

    tests = load_test_cases()

    print(
        f"Đã tải thành công "
        f"{len(tests)} Test Cases thử nghiệm.\n"
    )

    # =============================================================
    # INTERACTIVE MODE
    # =============================================================

    if "--interactive" in sys.argv:

        print(
            "[INTERACTIVE MODE] "
            "Trò chuyện trực tiếp với ReAct Agent:"
        )

        print(
            "Gợi ý câu hỏi thử nghiệm:"
        )

        print(
            "- Câu hỏi chung: "
            "'Quy chế học vụ VinUni yêu cầu bao nhiêu tín chỉ?'"
        )

        print(
            "- Tra cứu học vụ: "
            "'Hãy tra cứu thông tin học vụ "
            "của sinh viên SV2026001'"
        )

        print(
            "- Đặt lịch hẹn: "
            "'Đặt lịch hẹn tư vấn cho SV2026001 "
            "vào 14:00 ngày 15/09/2026'"
        )

        print(
            "- Gõ 'exit' hoặc 'quit' "
            "để kết thúc phiên trò chuyện.\n"
        )

        while True:

            try:

                user_input = input(
                    "Sinh viên hỏi: "
                ).strip()

                if (
                    not user_input
                    or user_input.lower()
                    in ["exit", "quit"]
                ):

                    print(
                        "Tạm biệt! "
                        "Kết thúc phiên trò chuyện."
                    )

                    break

                logs = run_react_agent(
                    user_input,
                    provider,
                    mcp_server
                )

                save_waterfall_trace(logs)

            except (
                KeyboardInterrupt,
                EOFError
            ):

                print(
                    "\nĐã thoát phiên tương tác."
                )

                break

    # =============================================================
    # TEST SUITE MODE
    # =============================================================

    elif "--all" in sys.argv:

        print(
            "[TEST SUITE MODE] "
            "Kiểm tra 5 Test Cases:"
        )

        completed_count = 0
        todo_count = 0

        all_traces = []

        for tc in tests:

            print(
                "\n=================================================="
            )

            print(
                f"[{tc['id']}] "
                f"Loại test: {tc['type']} "
                f"(Độ phức tạp: {tc['complexity']})"
            )

            print(
                f"Kỳ vọng: "
                f"{tc['expected_behavior']}"
            )

            if tc["question"].strip().startswith("TODO"):

                print(
                    "[CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:"
                )

                print(
                    tc["question"]
                )

                print(
                    "Hãy mở file "
                    "'config/test_cases.json' "
                    "để viết câu hỏi thực tế "
                    "cho Test Case này!"
                )

                todo_count += 1

            else:

                logs = run_react_agent(
                    tc["question"],
                    provider,
                    mcp_server
                )

                all_traces.extend(logs)

                completed_count += 1

        print(
            "\n=================================================="
        )

        print(
            f"[KẾT QUẢ TEST SUITE]: "
            f"Đã thực thi {completed_count}/{len(tests)} "
            f"Test Cases | "
            f"{todo_count} Test Cases "
            f"đang chờ điền câu hỏi (TODO)"
        )

        if all_traces:

            save_waterfall_trace(
                all_traces
            )

        print(
            "Để trò chuyện trực tiếp từng câu: "
            "Chạy 'python src/app.py --interactive'"
        )

    # =============================================================
    # DEFAULT MODE
    # =============================================================

    else:

        print(
            "HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:"
        )

        print(
            "1. Chat trực tiếp liên tục:   "
            "python src/app.py --interactive"
        )

        print(
            "2. Chạy toàn bộ Test Cases:    "
            "python src/app.py --all\n"
        )

        sample_query = tests[1]["question"]

        print(
            "--- DEMO CHẠY THỬ 1 TEST CASE MẪU "
            "(TC02: Tra cứu học vụ) ---"
        )

        logs = run_react_agent(
            sample_query,
            provider,
            mcp_server
        )

        save_waterfall_trace(
            logs
        )

        print(
            "\nHãy thử ngay lệnh: "
            "python src/app.py --interactive "
            "để chat trực tiếp!"
        )
