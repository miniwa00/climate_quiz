import gradio as gr
import json
import datetime
import os
import pandas as pd
import re

# 결과 파일 경로
RESULTS_FILE = "result.json"

# 결과 파일이 없으면 생성
if not os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE, "w") as f:
        json.dump([], f)

# TODO: Gemini API 설정 (API 키 등)
# 예: from google.generativeai import GenerativeModel

# 전역 변수로 현재 퀴즈 목록과 현재 퀴즈 인덱스 관리
current_quizzes = []
current_quiz_index = 0
user_answers = {}


def generate_quiz():
    """
    세 개의 JSON 파일에서 문제를 가져와 랜덤으로 섞어서 퀴즈를 생성합니다.
    climate.json: 4문제, poverty.json: 3문제, inequalities.json: 3문제
    """
    global current_quizzes, current_quiz_index, user_answers
    # TODO: Gemini API를 호출하여 실제 퀴즈 데이터를 가져옵니다.

    import random

    try:
        # 각 파일에서 문제 로드
        with open("climate.json", "r") as f:
            climate_quizzes = json.load(f)
        with open("poverty.json", "r") as f:
            poverty_quizzes = json.load(f)
        with open("inequalities.json", "r") as f:
            inequalities_quizzes = json.load(f)

        # 각 카테고리에서 지정된 수만큼 랜덤 선택
        selected_climate = random.sample(climate_quizzes, min(4, len(climate_quizzes)))
        selected_poverty = random.sample(poverty_quizzes, min(3, len(poverty_quizzes)))
        selected_inequalities = random.sample(
            inequalities_quizzes, min(3, len(inequalities_quizzes))
        )

        # 모든 문제를 합치고 랜덤으로 섞기
        current_quizzes = selected_climate + selected_poverty + selected_inequalities
        random.shuffle(current_quizzes)

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading quiz files: {e}")
        current_quizzes = []

    current_quiz_index = 0
    user_answers = {}  # 새 퀴즈 생성 시 사용자 답변 초기화

    # UI 상태 업데이트
    initial_landing_image_update = gr.update(visible=False)
    quiz_area_update = gr.update(visible=True)
    results_display_area_update = gr.update(visible=False)
    quiz_status_msg_update = gr.update(value="")
    submission_feedback_update = gr.update(value="")
    final_explanation_display_update = gr.update(value="")
    submit_area_update = gr.update(visible=False)
    review_summary_display_update = gr.update(visible=False, value="")
    generate_btn_update = gr.update(
        interactive=False, visible=False
    )  # 퀴즈 시작 시 비활성화
    home_btn_in_quiz_view_update = gr.update(
        visible=True, interactive=True
    )  # 퀴즈 중 홈 버튼 활성화

    if not current_quizzes:
        return (
            gr.update(visible=True),  # initial_landing_image (유지)
            gr.update(visible=False),  # quiz_area (숨김)
            gr.update(visible=False),  # results_display_area (숨김)
            gr.update(
                value="Failed to generate quizzes. Please check if all quiz files (climate.json, poverty.json, inequalities.json) exist."
            ),  # quiz_status_msg
            generate_btn_update,  # 현재 상태(비활성) 유지
            home_btn_in_quiz_view_update,  # 현재 상태(활성) 유지
            gr.update(value="Press 'Take Quiz' to start."),  # quiz_question
            gr.update(choices=[], value=None),  # quiz_options
            gr.update(interactive=False, visible=True),  # prev_btn
            gr.update(interactive=False, visible=True),  # next_btn
            gr.update(interactive=False, visible=False),  # review_complete_btn
            submit_area_update,
            gr.update(value=""),  # user_name_input
            gr.update(value=None),  # user_age_input
            gr.update(value=""),  # user_country_input
            gr.update(interactive=False),  # submit_btn
            review_summary_display_update,
            submission_feedback_update,  # 결과 영역내 컴포넌트 초기화
            final_explanation_display_update,  # 결과 영역내 컴포넌트 초기화
        )

    first_quiz_display_outputs = display_quiz(0)  # 이제 12개 항목 반환

    return (
        initial_landing_image_update,  # 1
        quiz_area_update,  # 2
        results_display_area_update,  # 3
        quiz_status_msg_update,  # 4
        generate_btn_update,  # 현재 상태(비활성) 유지
        home_btn_in_quiz_view_update,  # 현재 상태(활성) 유지
        first_quiz_display_outputs[0],  # quiz_question (display_quiz[0]) #7
        first_quiz_display_outputs[2],  # quiz_options (display_quiz[2]) #8
        first_quiz_display_outputs[3],  # prev_btn (display_quiz[3]) #9
        first_quiz_display_outputs[4],  # next_btn (display_quiz[4]) #10
        first_quiz_display_outputs[5],  # review_complete_btn (display_quiz[5]) #11
        first_quiz_display_outputs[6],  # submit_area (display_quiz[6]) #12
        first_quiz_display_outputs[7],  # user_name_input (display_quiz[7]) #13
        first_quiz_display_outputs[8],  # user_age_input (display_quiz[8]) #14
        first_quiz_display_outputs[9],  # user_country_input (display_quiz[9]) #15
        first_quiz_display_outputs[10],  # submit_btn (display_quiz[10]) #16
        first_quiz_display_outputs[11],  # review_summary_display (display_quiz[11]) #17
        submission_feedback_update,  # 18
        final_explanation_display_update,  # 19
    )


def display_quiz(index):
    """
    현재 인덱스에 해당하는 퀴즈를 표시합니다. (12개 항목 반환)
    """
    global current_quizzes, current_quiz_index
    submit_area_update = gr.update(visible=False)
    review_summary_display_update = gr.update(value="", visible=False)

    if not current_quizzes or not (0 <= index < len(current_quizzes)):
        return (
            gr.update(value="No quiz available."),  # quiz_question
            gr.update(value=""),  # quiz_status_msg (빈 값)
            gr.update(choices=[], value=None),  # quiz_options
            gr.update(interactive=False, visible=True),  # prev_btn
            gr.update(interactive=False, visible=True),  # next_btn
            gr.update(interactive=False, visible=False),  # review_complete_btn
            submit_area_update,
            gr.update(value=""),  # user_name_input
            gr.update(value=None),  # user_age_input
            gr.update(value=""),  # user_country_input
            gr.update(interactive=False),  # submit_btn 초기화
            review_summary_display_update,
        )

    current_quiz_index = index
    quiz = current_quizzes[index]
    question_text = f"Quiz {index + 1}/{len(current_quizzes)}: {quiz['question']}"
    options = quiz["options"]
    current_answer = user_answers.get(index)
    quiz_options_update = gr.update(
        choices=options, value=current_answer, interactive=True
    )

    prev_btn_interactive = index > 0
    is_last_quiz = index == len(current_quizzes) - 1

    prev_btn_update = gr.update(interactive=prev_btn_interactive, visible=True)
    next_btn_update = gr.update(interactive=not is_last_quiz, visible=not is_last_quiz)
    review_complete_btn_update = gr.update(
        interactive=is_last_quiz, visible=is_last_quiz
    )

    return (
        question_text,  # 1
        "",  # quiz_status_msg #2
        quiz_options_update,  # 3
        prev_btn_update,  # 4
        next_btn_update,  # 5
        review_complete_btn_update,  # 6
        submit_area_update,  # 7 기본적으로 숨김, handle_review_complete에서 표시
        gr.update(value=""),  # 8 user_name_input 초기화
        gr.update(value=None),  # 9 user_age_input 초기화
        gr.update(value=""),  # 10 user_country_input 초기화
        gr.update(interactive=False),  # 11 submit_btn 초기화
        review_summary_display_update,  # 12 기본적으로 숨김, handle_review_complete에서 표시
    )


def prev_quiz():
    """이전 퀴즈로 이동합니다."""
    global current_quiz_index
    if current_quiz_index > 0:
        return display_quiz(current_quiz_index - 1)
    return display_quiz(current_quiz_index)  # 변경 없음


def next_quiz():
    """다음 퀴즈로 이동합니다."""
    global current_quiz_index, current_quizzes
    if current_quiz_index < len(current_quizzes) - 1:
        return display_quiz(current_quiz_index + 1)
    return display_quiz(current_quiz_index)  # 변경 없음


def store_answer(answer):
    """사용자의 답변을 저장합니다."""
    global user_answers, current_quiz_index
    if answer is not None:
        user_answers[current_quiz_index] = answer
    return None  # 아무것도 반환하지 않음 (또는 빈 튜플)


def handle_review_complete():
    """'검토 완료' 버튼 클릭 시 호출됩니다."""
    global current_quizzes, user_answers

    if not current_quizzes:
        return (
            gr.update(value="Error: No quiz data to review.", visible=True),
            gr.update(visible=False),
            gr.update(value=""),
            gr.update(value=None),
            gr.update(value=""),
            gr.update(interactive=False),
            gr.update(visible=False, interactive=False),
        )

    review_text = "## 🧐 Please confirm your answers:\n\n"
    for i, quiz_data in enumerate(current_quizzes):
        user_ans = user_answers.get(i)
        review_text += f"### **Quiz {i+1}. {quiz_data['question']}**\n"
        review_text += (
            f"  \n- Your answer: {user_ans if user_ans else 'Not selected'}\n"
        )
        # review_text += "---" # 사용자가 주석 처리한 부분 유지

    return (
        gr.update(value=review_text, visible=True),  # review_summary_display
        gr.update(visible=True),  # submit_area
        gr.update(value=""),  # user_name_input 초기화
        gr.update(value=None),  # user_age_input 초기화
        gr.update(value=""),  # user_country_input 초기화
        gr.update(interactive=True),  # submit_btn 활성화
        gr.update(visible=False, interactive=False),  # review_complete_btn 숨기기
    )


def submit_quiz(name, age, country):
    """
    퀴즈를 제출하고 점수를 계산하여 저장합니다.
    """
    global current_quizzes, user_answers, current_quiz_index

    quiz_status_msg_update = gr.update()
    submission_feedback_update = gr.update()
    final_explanation_display_update = gr.update()
    leaderboard_update = gr.update()  # 성공 시에만 업데이트
    generate_btn_update = gr.update(
        interactive=False
    )  # 제출 후에도 퀴즈풀기 버튼은 비활성
    home_btn_in_quiz_view_update = gr.update(
        visible=False, interactive=False
    )  # 결과화면에선 이 버튼 숨김

    if not name or not age or not country:
        quiz_status_msg_update = gr.update(
            value="# ⚠️ Please fill in all fields (name, age, country)."
        )
        # 정보 미입력 시, 현재 UI (quiz_area 내 submit_area) 유지
        return (
            gr.update(visible=False),  # initial_landing_image
            gr.update(visible=True),  # quiz_area (유지)
            gr.update(visible=False),  # results_display_area
            quiz_status_msg_update,
            submission_feedback_update,  # 내용 변경 없음
            final_explanation_display_update,  # 내용 변경 없음
            generate_btn_update,  # 현재 상태(비활성) 유지
            leaderboard_update,  # 변경 없음
            home_btn_in_quiz_view_update,  # 현재 상태(활성) 유지
        )

    if not current_quizzes:
        quiz_status_msg_update = gr.update(
            value="No quiz to submit. Please generate a new quiz."
        )
        # 퀴즈 없으면 초기화면으로 (generate_btn 활성, home_btn_in_quiz_view 비활성)
        return (
            gr.update(visible=True),  # initial_landing_image (표시)
            gr.update(visible=False),  # quiz_area (숨김)
            gr.update(visible=False),  # results_display_area (숨김)
            quiz_status_msg_update,
            submission_feedback_update,
            final_explanation_display_update,
            leaderboard_update,
            gr.update(interactive=True, visible=True),  # generate_btn 활성화
            gr.update(visible=False, interactive=False),  # home_btn_in_quiz_view 숨김
        )

    score = 0
    detailed_explanation_text = "\n---\n## 🧐 Results and Explanations\n\n"
    for i, quiz_data in enumerate(current_quizzes):
        user_ans = user_answers.get(i)
        correct_ans = quiz_data["answer"]
        explanation = quiz_data.get("explanation", "No explanation available.")
        is_correct = user_ans == correct_ans
        if is_correct:
            score += 1

        detailed_explanation_text += f"### **Quiz {i+1}. {quiz_data['question']}**\n"
        detailed_explanation_text += (
            f"  - Your answer: {user_ans if user_ans else 'Not selected'}\n"
        )
        detailed_explanation_text += f"  - Correct Answer: {correct_ans}\n"
        detailed_explanation_text += (
            f"  - Result: {'**Correct** ✅' if is_correct else '**Incorrect** ❌'}\n"
        )
        detailed_explanation_text += f"  - Explanation: {explanation}\n---\n"

    total_questions = len(current_quizzes)
    percentage_score = (
        int((score / total_questions) * 100) if total_questions > 0 else 0
    )
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(RESULTS_FILE, "r") as f:
            results_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        results_data = []

    results_data.append(
        {
            "name": name,
            "age": int(age),
            "country": country,
            "score": f"{score}/{total_questions} ({percentage_score}%)",
            "timestamp": timestamp,
        }
    )

    with open(RESULTS_FILE, "w") as f:
        json.dump(results_data, f, indent=4)

    submission_feedback_update = gr.update(
        value=f"## 🎉 Congratulations, {name}! Submission complete!\n ## Final Score: {score}/{total_questions} ({percentage_score:.2f}%) 🎉"
    )
    final_explanation_display_update = gr.update(value=detailed_explanation_text)
    leaderboard_update = load_leaderboard()  # DataFrame 또는 리스트의 리스트 반환
    quiz_status_msg_update = gr.update(value="")  # 이전 상태 메시지 클리어

    # 전역 퀴즈 데이터 초기화
    current_quizzes.clear()
    user_answers.clear()
    current_quiz_index = 0

    return (
        gr.update(visible=False),  # initial_landing_image
        gr.update(visible=False),  # quiz_area
        gr.update(visible=True),  # results_display_area
        quiz_status_msg_update,
        submission_feedback_update,
        final_explanation_display_update,
        leaderboard_update,
        generate_btn_update,  # 제출 성공 후 퀴즈풀기 버튼 비활성 유지
        home_btn_in_quiz_view_update,  # 제출 성공 후 이 버튼 숨김
    )


def load_leaderboard():
    """리더보드 데이터를 로드하여 순위 매기기 및 정렬 후 DataFrame 호환 형태로 반환합니다."""
    try:
        with open(RESULTS_FILE, "r") as f:
            results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        results = []

    if not results:
        return pd.DataFrame(
            columns=["Rank", "Name", "Age", "Country", "Score", "Timestamp"]
        )

    # 점수 추출 및 정수 변환 (예: "3/5" -> 3)
    for res in results:
        match = re.match(r"(\d+)/\d+", res["score"])
        res["numeric_score"] = int(match.group(1)) if match else 0

    # 점수(내림차순), 시간(내림차순 - 최신이 위로) 기준으로 정렬
    results.sort(key=lambda x: (x["numeric_score"], x["timestamp"]), reverse=True)

    leaderboard_data = []
    rank_counter = 0
    prev_score = -1  # 나올 수 없는 점수로 초기화
    count_for_rank_tie = 0  # 현재 순위 동점자 수 (자신 포함)

    for i, res in enumerate(results):
        current_score = res["numeric_score"]
        if current_score != prev_score:
            rank_counter += count_for_rank_tie  # 이전 동점자 수만큼 순위 증가
            count_for_rank_tie = 1  # 현재 항목으로 동점자 수 초기화
            actual_rank_display = rank_counter + 1  # 실제 표시 순위 (1부터 시작)
        else:
            count_for_rank_tie += 1
            actual_rank_display = rank_counter + 1  # 동점자는 같은 순위

        leaderboard_data.append(
            [
                f"{actual_rank_display}",
                res["name"],
                str(res.get("age", "N/A")),
                res.get("country", "N/A"),
                res["score"],  # 원본 점수 문자열 표시
                res["timestamp"],
            ]
        )
        prev_score = current_score

    return leaderboard_data


def clear_leaderboard():
    """리더보드 데이터를 초기화합니다."""
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "w") as f:
            json.dump([], f)
    return load_leaderboard()


def return_to_home():
    """홈으로 돌아가기 버튼 클릭 시 호출 (결과 화면에서)"""
    # UI 초기 상태로 복원
    quiz_question_update = gr.update(value="Press 'Take Quiz' to start.")
    quiz_options_update = gr.update(choices=[], value=None, interactive=True)
    prev_btn_update = gr.update(interactive=False, visible=True)
    next_btn_update = gr.update(interactive=False, visible=True)
    review_complete_btn_update = gr.update(interactive=False, visible=False)
    review_summary_display_update = gr.update(value="", visible=False)
    submit_area_update = gr.update(visible=False)
    user_name_input_update = gr.update(value="")
    user_age_input_update = gr.update(value=None)
    user_country_input_update = gr.update(value="")
    submit_btn_update = gr.update(interactive=False)
    quiz_status_msg_update = gr.update(value="")
    submission_feedback_update = gr.update(value="")
    final_explanation_display_update = gr.update(value="")
    generate_btn_update = gr.update(
        interactive=True,
        visible=True,
    )  # 홈으로 돌아오면 퀴즈풀기 버튼 활성화
    home_btn_in_quiz_view_update = gr.update(
        visible=False,
        interactive=False,
    )  # 이 버튼은 숨김

    # 전역 변수 초기화도 필요할 수 있음 (퀴즈 중단과 유사)
    global current_quizzes, user_answers, current_quiz_index
    current_quizzes = []
    user_answers = {}
    current_quiz_index = 0

    return (
        gr.update(visible=True),  # initial_landing_image
        gr.update(visible=False),  # quiz_area
        gr.update(visible=False),  # results_display_area
        quiz_status_msg_update,
        generate_btn_update,
        home_btn_in_quiz_view_update,
        quiz_question_update,
        quiz_options_update,
        prev_btn_update,
        next_btn_update,
        review_complete_btn_update,
        submit_area_update,
        user_name_input_update,
        user_age_input_update,
        user_country_input_update,
        submit_btn_update,
        review_summary_display_update,
        submission_feedback_update,
        final_explanation_display_update,
    )


def go_to_home_from_quiz_view():
    """퀴즈 푸는 도중 홈으로 돌아가기 버튼 클릭 시 호출"""
    # return_to_home과 거의 동일한 로직, 전역 변수 초기화 포함
    global current_quizzes, user_answers, current_quiz_index
    current_quizzes = []
    user_answers = {}
    current_quiz_index = 0

    quiz_question_update = gr.update(value="Press 'Take Quiz' to start.")
    quiz_options_update = gr.update(choices=[], value=None, interactive=True)
    prev_btn_update = gr.update(interactive=False, visible=True)
    next_btn_update = gr.update(interactive=False, visible=True)
    review_complete_btn_update = gr.update(interactive=False, visible=False)
    review_summary_display_update = gr.update(value="", visible=False)
    submit_area_update = gr.update(visible=False)
    user_name_input_update = gr.update(value="")
    user_age_input_update = gr.update(value=None)
    user_country_input_update = gr.update(value="")
    submit_btn_update = gr.update(interactive=False)
    quiz_status_msg_update = gr.update(value="")
    submission_feedback_update = gr.update(value="")
    final_explanation_display_update = gr.update(value="")
    generate_btn_update = gr.update(
        interactive=True,
        visible=True,
    )  # 홈으로 돌아오면 퀴즈풀기 버튼 활성화
    home_btn_in_quiz_view_update = gr.update(
        visible=False, interactive=False
    )  # 이 버튼은 숨김

    return (
        gr.update(visible=True),  # initial_landing_image
        gr.update(visible=False),  # quiz_area
        gr.update(visible=False),  # results_display_area
        quiz_status_msg_update,
        generate_btn_update,
        home_btn_in_quiz_view_update,
        quiz_question_update,
        quiz_options_update,
        prev_btn_update,
        next_btn_update,
        review_complete_btn_update,
        submit_area_update,
        user_name_input_update,
        user_age_input_update,
        user_country_input_update,
        submit_btn_update,
        review_summary_display_update,
        submission_feedback_update,
        final_explanation_display_update,
    )


# Gradio 인터페이스 정의
with gr.Blocks(
    theme=gr.themes.Soft(),
    css="""
    * {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
    }
    """,
) as demo:
    gr.Markdown("# My SDG Compass 🌍")

    tabs = gr.Tabs()
    with tabs:
        with gr.TabItem("Take Quiz"):
            initial_landing_image = gr.Image(
                "start.png",
                elem_id="landing_image",
                width=500,
                visible=True,
                show_label=False,
                show_download_button=False,
                show_fullscreen_button=False,
            )

            with gr.Row():
                generate_btn = gr.Button(
                    "Take Quiz",
                    variant="primary",
                    scale=1,
                )
                home_btn_in_quiz_view = gr.Button(
                    "Return to Home",
                    variant="stop",
                    visible=False,
                    interactive=False,
                    scale=1,
                )

            quiz_status_msg = gr.Markdown(
                ""
            )  # 퀴즈 생성 실패, 이름 입력 요청 등 주요 상태 메시지

            with gr.Column(visible=False) as quiz_area:
                quiz_question = gr.Markdown("Press 'Take Quiz' to start.")
                quiz_options = gr.Radio(
                    label="Choose your answer", choices=[], interactive=True
                )
                with gr.Row():
                    prev_btn = gr.Button("Previous Question", interactive=False)
                    next_btn = gr.Button("Next Question", interactive=False)
                    review_complete_btn = gr.Button(
                        "Review Complete", interactive=False, visible=False
                    )
                review_summary_display = gr.Markdown(visible=False)
                with gr.Column(visible=False) as submit_area:
                    user_name_input = gr.Textbox(
                        label="Enter your name:", placeholder="e.g., John Doe"
                    )
                    user_age_input = gr.Number(
                        label="Enter your age (1-120):",
                        minimum=1,
                        maximum=120,
                        precision=0,
                    )
                    user_country_input = gr.Textbox(
                        label="Enter your country:", placeholder="e.g., South Korea"
                    )
                    submit_btn = gr.Button(
                        "Submit", variant="primary", interactive=False
                    )

            with gr.Column(visible=False) as results_display_area:
                end_image = gr.Image(
                    "end.png",
                    elem_id="end_image",
                    width=500,
                    visible=True,
                    show_label=False,
                    show_download_button=False,
                    show_fullscreen_button=False,
                )
                submission_feedback = gr.Markdown("")  # 최종 점수 요약
                final_explanation_display = gr.Markdown("")  # 문제별 해설
                return_to_home_btn = gr.Button("Return to Home", variant="secondary")

        with gr.TabItem("Leaderboard"):
            with gr.Row():
                refresh_leaderboard_btn = gr.Button("Refresh Leaderboard")
                clear_leaderboard_btn = gr.Button("⚠️ Reset Leaderboard", variant="stop")
            leaderboard_display = gr.DataFrame(
                value=load_leaderboard(),
                headers=["Rank", "Name", "Age", "Country", "Score", "Timestamp"],
                datatype=["str", "str", "str", "str", "str", "str"],
                interactive=False,
            )

    # 탭 선택 이벤트 - Leaderboard 탭 선택 시 자동 새로고침
    def handle_tab_select(selected_tab):
        if selected_tab == 1:  # Leaderboard 탭 인덱스 (0: Take Quiz, 1: Leaderboard)
            return load_leaderboard()
        return gr.update()

    tabs.select(handle_tab_select, outputs=[leaderboard_display])

    # 퀴즈 생성 버튼 클릭 이벤트
    generate_btn.click(
        generate_quiz,
        outputs=[
            initial_landing_image,
            quiz_area,
            results_display_area,
            quiz_status_msg,
            generate_btn,
            home_btn_in_quiz_view,
            quiz_question,
            quiz_options,
            prev_btn,
            next_btn,
            review_complete_btn,
            submit_area,
            user_name_input,
            user_age_input,
            user_country_input,
            submit_btn,
            review_summary_display,
            submission_feedback,
            final_explanation_display,
        ],
    )

    # 이전/다음 버튼은 display_quiz의 반환값(12개)을 정확히 매핑해야 함
    quiz_navigation_outputs = [
        quiz_question,
        quiz_status_msg,  # display_quiz에서 오는 빈 문자열을 받음
        quiz_options,
        prev_btn,
        next_btn,
        review_complete_btn,
        submit_area,
        user_name_input,
        user_age_input,
        user_country_input,
        submit_btn,
        review_summary_display,
    ]

    prev_btn.click(prev_quiz, outputs=quiz_navigation_outputs)
    next_btn.click(next_quiz, outputs=quiz_navigation_outputs)

    # 라디오 버튼(정답 선택) 변경 시 사용자 답변 저장
    quiz_options.change(store_answer, inputs=[quiz_options], outputs=[])

    # 검토 완료 버튼 클릭 이벤트
    review_complete_btn.click(
        handle_review_complete,
        outputs=[
            review_summary_display,
            submit_area,
            user_name_input,
            user_age_input,
            user_country_input,
            submit_btn,
            review_complete_btn,
        ],
    )

    # 제출하기 버튼 클릭 이벤트
    submit_btn.click(
        submit_quiz,
        inputs=[user_name_input, user_age_input, user_country_input],
        outputs=[
            initial_landing_image,
            quiz_area,
            results_display_area,
            quiz_status_msg,
            submission_feedback,
            final_explanation_display,
            leaderboard_display,
            generate_btn,
            home_btn_in_quiz_view,
        ],
    )

    # 홈으로 돌아가기 버튼 클릭 이벤트 (퀴즈 화면에서)
    home_btn_in_quiz_view.click(
        go_to_home_from_quiz_view,
        outputs=[
            initial_landing_image,
            quiz_area,
            results_display_area,
            quiz_status_msg,
            generate_btn,
            home_btn_in_quiz_view,
            quiz_question,
            quiz_options,
            prev_btn,
            next_btn,
            review_complete_btn,
            submit_area,
            user_name_input,
            user_age_input,
            user_country_input,
            submit_btn,
            review_summary_display,
            submission_feedback,
            final_explanation_display,
        ],
    )

    # 홈으로 돌아가기 버튼 클릭 이벤트 (결과 화면에서)
    return_to_home_btn.click(
        return_to_home,
        outputs=[
            initial_landing_image,
            quiz_area,
            results_display_area,
            quiz_status_msg,
            generate_btn,
            home_btn_in_quiz_view,
            quiz_question,
            quiz_options,
            prev_btn,
            next_btn,
            review_complete_btn,
            submit_area,
            user_name_input,
            user_age_input,
            user_country_input,
            submit_btn,
            review_summary_display,
            submission_feedback,
            final_explanation_display,
        ],
    )

    # 리더보드 새로고침 버튼
    refresh_leaderboard_btn.click(load_leaderboard, outputs=[leaderboard_display])
    clear_leaderboard_btn.click(clear_leaderboard, outputs=[leaderboard_display])

if __name__ == "__main__":
    demo.launch(share=False, server_name="0.0.0.0", server_port=7862)
