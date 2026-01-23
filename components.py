"""
このファイルは、画面表示に特化した関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import streamlit as st
import utils
import constants as ct


############################################################
# 追加：表示用ユーティリティ
############################################################
def _is_pdf(path: str) -> bool:
    if not isinstance(path, str):
        return False
    return path.lower().endswith(".pdf")


def _format_source_with_page(path: str, page_no: int | None) -> str:
    """
    PDFのときだけページNo.を付与して表示する。
    表示形式: "<path>（ページNo. X）"
    """
    if _is_pdf(path) and page_no is not None:
        return f"{path}（ページNo. {page_no}）"
    return path


############################################################
# 関数定義
############################################################

def display_app_title():
    """
    タイトル表示
    """
    st.markdown(f"<h1 style='text-align:center;'>{ct.APP_NAME}</h1>", unsafe_allow_html=True)


def display_initial_ai_message():
    """
    AIメッセージの初期表示（緑文字＋薄緑背景）
    """
    with st.chat_message("assistant"):
        st.markdown(
            """
            <div style="
                background-color: #e8f5e9;
                color: #2e7d32;
                padding: 12px 16px;
                border-radius: 8px;
                line-height: 1.6;
                font-weight: 500;
            ">
                こんにちは。私は社内文書の情報をもとに回答する生成AIチャットボットです。<br>
                サイドバーで利用目的を選択し、画面下部のチャット欄からメッセージを送信してください。
            </div>
            """,
            unsafe_allow_html=True
        )


def display_conversation_log():
    """
    会話ログの一覧表示
    """
    # 会話ログのループ処理
    for message in st.session_state.messages:
        # 「message」辞書の中の「role」キーには「user」か「assistant」が入っている
        with st.chat_message(message["role"]):

            # ユーザー入力値の場合、そのままテキストを表示するだけ
            if message["role"] == "user":
                st.markdown(message["content"])

            # LLMからの回答の場合
            else:
                # 「社内文書検索」の場合、テキストの種類に応じて表示形式を分岐処理
                if message["content"]["mode"] == ct.ANSWER_MODE_1:

                    # ファイルのありかの情報が取得できた場合（通常時）の表示処理
                    if not "no_file_path_flg" in message["content"]:
                        # ==========================================
                        # ユーザー入力値と最も関連性が高いメインドキュメントのありかを表示
                        # ==========================================
                        # 補足文の表示
                        st.markdown(message["content"]["main_message"])

                        main_path = message["content"]["main_file_path"]
                        icon = utils.get_source_icon(main_path)

                        # ✅ PDFだけページNo.を表示
                        main_page = message["content"].get("main_page_number")  # 既に表示用(1始まり)で保存される想定
                        st.success(_format_source_with_page(main_path, main_page), icon=icon)

                        # ==========================================
                        # ユーザー入力値と関連性が高いサブドキュメントのありかを表示
                        # ==========================================
                        if "sub_message" in message["content"]:
                            # 補足メッセージの表示
                            st.markdown(message["content"]["sub_message"])

                            # サブドキュメントのありかを一覧表示
                            for sub_choice in message["content"]["sub_choices"]:
                                sub_path = sub_choice["source"]
                                icon = utils.get_source_icon(sub_path)

                                # ✅ PDFだけページNo.を表示
                                sub_page = sub_choice.get("page_number")  # 既に表示用(1始まり)で保存される想定
                                st.info(_format_source_with_page(sub_path, sub_page), icon=icon)

                    # ファイルのありかの情報が取得できなかった場合、LLMからの回答のみ表示
                    else:
                        st.markdown(message["content"]["answer"])

                # 「社内問い合わせ」の場合の表示処理
                else:
                    # LLMからの回答を表示
                    st.markdown(message["content"]["answer"])

                    # 参照元のありかを一覧表示
                    if "file_info_list" in message["content"]:
                        # 区切り線の表示
                        st.divider()
                        # 「情報源」の文字を太字で表示
                        st.markdown(f"##### {message['content']['message']}")
                        # ドキュメントのありかを一覧表示
                        for file_info in message["content"]["file_info_list"]:
                            # 参照元のありかに応じて、適したアイコンを取得
                            icon = utils.get_source_icon(file_info)
                            st.info(file_info, icon=icon)


def display_search_llm_response(llm_response):
    """
    「社内文書検索」モードにおけるLLMレスポンスを表示

    Args:
        llm_response: LLMからの回答

    Returns:
        LLMからの回答を画面表示用に整形した辞書データ
    """
    # LLMからのレスポンスに参照元情報が入っており、かつ「該当資料なし」が回答として返された場合
    if llm_response["context"] and llm_response["answer"] != ct.NO_DOC_MATCH_ANSWER:

        # ==========================================
        # ユーザー入力値と最も関連性が高いメインドキュメントのありかを表示
        # ==========================================
        main_doc = llm_response["context"][0]
        main_file_path = main_doc.metadata["source"]

        # 補足メッセージの表示
        main_message = "入力内容に関する情報は、以下のファイルに含まれている可能性があります。"
        st.markdown(main_message)

        icon = utils.get_source_icon(main_file_path)

        # ✅ PDFだけページNo.を表示（PyMuPDFLoader は 0始まりが多いので +1 で表示）
        main_page_number_disp = None
        if _is_pdf(main_file_path) and "page" in main_doc.metadata:
            main_page_number_disp = int(main_doc.metadata["page"]) + 1

        st.success(_format_source_with_page(main_file_path, main_page_number_disp), icon=icon)

        # ==========================================
        # ユーザー入力値と関連性が高いサブドキュメントのありかを表示
        # ==========================================
        sub_choices = []
        duplicate_check_list = []

        for document in llm_response["context"][1:]:
            sub_file_path = document.metadata["source"]

            if sub_file_path == main_file_path:
                continue
            if sub_file_path in duplicate_check_list:
                continue
            duplicate_check_list.append(sub_file_path)

            # ✅ PDFだけページNo.を保持（表示用に +1 した値を保存）
            if _is_pdf(sub_file_path) and "page" in document.metadata:
                sub_page_number_disp = int(document.metadata["page"]) + 1
                sub_choice = {"source": sub_file_path, "page_number": sub_page_number_disp}
            else:
                sub_choice = {"source": sub_file_path}

            sub_choices.append(sub_choice)

        if sub_choices:
            sub_message = "その他、ファイルありかの候補を提示します。"
            st.markdown(sub_message)

            for sub_choice in sub_choices:
                icon = utils.get_source_icon(sub_choice["source"])
                st.info(
                    _format_source_with_page(sub_choice["source"], sub_choice.get("page_number")),
                    icon=icon
                )

        # 表示用の会話ログに格納するためのデータを用意
        content = {}
        content["mode"] = ct.ANSWER_MODE_1
        content["main_message"] = main_message
        content["main_file_path"] = main_file_path

        # ✅ PDFだけページNo.（表示用）を保持
        if main_page_number_disp is not None:
            content["main_page_number"] = main_page_number_disp

        if sub_choices:
            content["sub_message"] = sub_message
            content["sub_choices"] = sub_choices

    else:
        st.markdown(ct.NO_DOC_MATCH_MESSAGE)

        content = {}
        content["mode"] = ct.ANSWER_MODE_1
        content["answer"] = ct.NO_DOC_MATCH_MESSAGE
        content["no_file_path_flg"] = True

    return content


def display_contact_llm_response(llm_response):
    """
    「社内問い合わせ」モードにおけるLLMレスポンスを表示

    Args:
        llm_response: LLMからの回答

    Returns:
        LLMからの回答を画面表示用に整形した辞書データ
    """
    st.markdown(llm_response["answer"])

    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER:
        st.divider()

        message = "情報源"
        st.markdown(f"##### {message}")

        file_path_list = []
        file_info_list = []

        for document in llm_response["context"]:
            file_path = document.metadata["source"]
            if file_path in file_path_list:
                continue

            # 既存仕様のまま（ここは要件外なので変更しない）
            if "page" in document.metadata:
                file_info = f"{file_path}"
            else:
                file_info = f"{file_path}"

            icon = utils.get_source_icon(file_path)
            st.info(file_info, icon=icon)

            file_path_list.append(file_path)
            file_info_list.append(file_info)

    content = {}
    content["mode"] = ct.ANSWER_MODE_2
    content["answer"] = llm_response["answer"]
    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER:
        content["message"] = message
        content["file_info_list"] = file_info_list

    return content


def display_sidebar():
    """
    サイドバーに「利用目的」と説明ブロックを表示
    """
    with st.sidebar:
        st.markdown("### 利用目的")

        st.session_state.mode = st.radio(
            label="",
            options=[ct.ANSWER_MODE_1, ct.ANSWER_MODE_2],
            label_visibility="collapsed"
        )

        st.divider()

        st.markdown(f"#### 「{ct.ANSWER_MODE_1}」を選択した場合")
        st.info("入力内容と関連性が高い社内文書のありかを検索できます。")
        st.code("【入力例】\n社員の育成方針に関するMTGの議事録", wrap_lines=True, language=None)

        st.markdown("---")

        st.markdown(f"#### 「{ct.ANSWER_MODE_2}」を選択した場合")
        st.info("質問・要望に対して、社内文書の情報をもとに回答を得られます。")
        st.code("【入力例】\n人事部に所属している従業員情報を一覧化して", wrap_lines=True, language=None)
