# coding=utf-8
import json
import hashlib
from datetime import datetime
import os
import time
import openai
import flet as ft
import re

from flet import (
    ElevatedButton,
    FilePicker,
    FilePickerResultEvent,
    Page,
    Row,
    Text,
    icons,
)


# 赋值固定的api_key
# 测试用
openai.api_key = None


'''
每一行对话的类
在调用的同时，会将数据存入聊天记录文件
'''


class chat_row(ft.UserControl):
    def __init__(self, role, content):
        super(chat_row, self).__init__()
        self.role = role
        self.content = content
        self.hash = save_now_chat(
            chat_json_path=chat_json_path,
            role=self.role,
            content=self.content)

    def build(self):
        self.role_dropdown = ft.Dropdown(
            value=self.role,
            width=150,
            options=[
                ft.dropdown.Option("system"),
                ft.dropdown.Option("user"),
                ft.dropdown.Option("assistant"),
            ],
            on_change=self.role_change

        )

        self.content_textfield = ft.TextField(
            value=self.content,
            filled=True,
            expand=True,
            multiline=True,
            on_change=self.content_change
        )

        return ft.Row(
            [
                self.role_dropdown,
                self.content_textfield,
            ]
        )

    def role_change(self, e):
        self.role = self.role_dropdown.value
        renew_now_chat(
            chat_json_path=chat_json_path,
            hash_val=self.hash,
            role=self.role)

    def content_change(self, e):
        self.content = self.content_textfield.value
        renew_now_chat(
            chat_json_path=chat_json_path,
            hash_val=self.hash,
            content=self.content)


'''
读写chatlog的相关函数
'''


# 创建chat数据记录的方法，将聊天数据结构基于 JSON 文件进行存储
def create_chat_json(save_path='./chatlog'):
    # 如果保存目录不存在，则创建目录
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # 获取当前时间并格式化为文件名格式
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    chat_json_name = f"chat_{now}.json"

    # 如果文件不存在，则创建文件
    chat_json_path = os.path.join(save_path, chat_json_name)
    if not os.path.exists(chat_json_path):
        with open(chat_json_path, 'w') as f:
            json.dump([], f, default=str)
    return chat_json_path


# 储存现有的每一句聊天信息
def save_now_chat(chat_json_path: str, role: str, content: str) -> str:
    '''
    将每一段聊天信息储存到一个 JSON 文件中。以哈希值作为唯一标识符
    :param chat_json_path: 聊天文件的路径
    :param role: 发言者
    :param content: 发言内容
    :return hash_val: 哈希值
    '''
    now = datetime.now().timestamp()
    str_to_hash = str(now) + role + content
    hash_obj = hashlib.blake2b(str_to_hash.encode('utf-8'), digest_size=8)
    hash_val = hash_obj.hexdigest()

    # 读取之前的内容
    try:
        with open(chat_json_path, 'r') as f:
            chats = json.load(f)
    except FileNotFoundError:
        chats = []

    # 添加新的聊天信息
    message = {
        'role': role,
        'content': content,
        'keyword': [],
        'summary': ''
    }
    chats.append({
        'chat_seq': len(chats) + 1,
        'hash': hash_val,
        'created_time': now,
        'altered_time': None,
        'message': message
    })

    # 将新的聊天信息写入文件
    with open(chat_json_path, 'w') as f:
        json.dump(chats, f, default=str)

    return hash_val


# 根据聊天信息的哈希值，更新现有历史聊天列表
def renew_now_chat(chat_json_path: str, hash_val: str,
                   role: str = None, content: str = None) -> None:
    '''
    根据聊天信息的哈希值，更新现有历史聊天列表
    :param chat_json_path: 聊天文件的路径
    :param hash_val: 聊天信息的哈希值
    :param role: 更新后的发言者（可选）
    :param content: 更新后的发言内容（可选）
    :return: None
    '''
    # 读取chat_renew_data.json文件
    with open(chat_json_path, 'r') as f:
        data = json.load(f)

    # 找出哈希值相同的键值对，并更新它们的role和content
    for chat_item in data:
        if hash_val == chat_item['hash']:
            if role:
                chat_item['message']['role'] = role
            if content:
                chat_item['message']['content'] = content
            chat_item["altered_time"] = datetime.now().timestamp()
            break

    # 将更新后的数据写回文件
    with open(chat_json_path, 'w') as f:
        json.dump(data, f, default=str)


# 根据聊天信息的哈希值，获取单个键值对内的role和content
def get_one_role_and_content(
        chat_json_path: str, hash_value: str) -> (str, str):
    '''
    根据聊天信息的哈希值，获取单个键值对内的role和content
    :param chat_json_path: 聊天文件的路径
    :param hash_value: 聊天信息的哈希值
    :return: (发言者, 发言内容)
    '''
    with open(chat_json_path) as f:
        data = json.load(f)

        for chat_item in data:
            for message in chat_item['message']:
                if hash_value == hashlib.blake2b(
                        str(message["created_time"] +
                            message["role"] +
                            message["content"]).encode('utf-8'),
                        digest_size=8).hexdigest():
                    return message["role"], message["content"]

        return None


# 读取特定文件内的所有role和content
def get_combined_data(chat_json_path: str) -> list[dict[str, str]]:
    '''
    获取特定文件内的所有role和content
    :param chat_json_path: JSON 聊天文件的路径
    :return: 包含所有发言者和发言内容的列表
    '''
    with open(chat_json_path) as f:
        data = json.load(f)
        result = []
        for chat_item in data:
            result.append({
                "role": chat_item['message']["role"],
                "content": chat_item['message']["content"]
            })
        return result


# 创建chat数据记录
chat_json_path = create_chat_json()


'''
读写API-KEY的函数
'''


# 定义 write_APIKEY 函数
def write_APIKEY(APIKEY=None):
    # 以追加模式打开或创建 APIKEY.txt 文件
    with open("APIKEY.txt", "a") as f:
        # 写入字符串并换行
        if APIKEY:
            f.write(APIKEY + "\n")


# 定义 read_APIKEY 函数
def read_APIKEY():
    # 以读取模式打开 APIKEY.txt 文件
    with open("APIKEY.txt", "r") as f:
        # 读取所有行并存入列表
        lines = f.readlines()
        # 如果列表不为空，返回最后一行的值，去掉换行符
        if lines:
            return lines[-1].strip()


'''
其他函数
'''


# 字符转码
def decode_chr(s):
    pattern = re.compile(r'(\\u[0-9a-fA-F]{4}|\n)')
    result = ''
    pos = 0
    while True:
        match = pattern.search(s, pos)
        if match is None:
            break
        result += s[pos:match.start()]
        if match.group() == '\n':
            result += '\n'
        else:
            result += chr(int(match.group()[2:], 16))
        pos = match.end()
    result += s[pos:]
    return result


# markdown检测
def markdown_check(gpt_msg):
    pass


'''
程序主窗体
'''


def ft_interface(page: ft.Page):
    # 设置字体与主题
    page.title = 'BillyGPT'
    page.fonts = {'A75方正像素12': './assets/font.ttf'}
    page.theme = ft.Theme(font_family='A75方正像素12')
    page.dark_theme = page.theme

    # 设置主页面聊天区域的滚动列表
    gpt_text = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
        padding=20)

    '''
    添加选择上传文件、保存文件、打开文件夹按钮
    '''
    # 导入聊天记录
    def pick_files_result(e: FilePickerResultEvent):
        try:
            gpt_text.controls.clear()
            selected_file = (
                ", ".join(map(lambda f: f.path, e.files)
                          ) if e.files else "Cancelled!"
            )
            full_chatlog = get_combined_data(selected_file)
            print(full_chatlog)
            for chat_row_content in full_chatlog:
                role = chat_row_content['role']
                content = chat_row_content['content']
                gpt_text.controls.append(chat_row(role, content))
                page.update()
        except Exception as e:
            gpt_text.controls.append(
                Text(f'出现如下报错\n{e}\n请检查导入的聊天记录是否正确，或联系开发者微信B1lli_official'))

    pick_files_dialog = FilePicker(on_result=pick_files_result)

    # 导出聊天记录（还没做）
    def save_file_result(e: FilePickerResultEvent):
        save_file_path.value = e.path if e.path else "Cancelled!"
        save_file_path.update()

    save_file_dialog = FilePicker(on_result=save_file_result)
    save_file_path = Text()

    # 打开文件夹（还没做）
    def get_directory_result(e: FilePickerResultEvent):
        directory_path.value = e.path if e.path else "Cancelled!"
        directory_path.update()

    get_directory_dialog = FilePicker(on_result=get_directory_result)
    directory_path = Text()

    # 隐藏所有
    page.overlay.extend(
        [pick_files_dialog, save_file_dialog, get_directory_dialog])

    '''
    添加设置对话和按钮
    '''
    def save_settings(e):
        settings_dlg.open = False
        write_APIKEY(apikey_field.value)
        read_APIKEY()
        page.update()

    def cancel_settings(e):
        settings_dlg.open = False
        page.update()

    apikey_field = ft.TextField(hint_text='在此输入apikey',)
    settings_dlg = ft.AlertDialog(
        title=ft.Text("Settings"),
        content=apikey_field,
        actions=[
            ft.TextButton("保存", on_click=save_settings),
            ft.TextButton("取消", on_click=cancel_settings)
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=10)
    )

    def open_dlg_modal(e):
        page.dialog = settings_dlg
        settings_dlg.open = True
        page.update()

    settings_btn = ft.IconButton(
        icon=ft.icons.SETTINGS_OUTLINED,
        icon_color="#9ecaff",
        bgcolor='#202429',
        icon_size=20,
        tooltip="Settings",
        on_click=open_dlg_modal,
    )

    '''
    添加启动应用程序获取apikey窗口
    '''
    def save_settings_open(e):
        open_setting_apikey_dlg.open = False
        write_APIKEY(apikey_field_open.value)
        openai.api_key = read_APIKEY()
        page.update()

    write_APIKEY()
    openai.api_key = read_APIKEY()
    if not openai.api_key:
        apikey_field_open = ft.TextField(label="输入你的apikey")
        open_setting_apikey_dlg = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text("欢迎使用BillyGPT"),
            content=ft.Column([apikey_field_open], tight=True),
            actions=[
                ft.ElevatedButton(
                    text="开始使用",
                    on_click=save_settings_open)],
            actions_alignment="end",
        )
        page.dialog = open_setting_apikey_dlg
        openai.api_key = read_APIKEY()


    '''
    添加聊天行
    '''
    def add_msg(e):
        gpt_text.controls.append(chat_row('user', chat_text.value))
        chat_text.value = ""
        page.update()
        gpt_text.controls.append(chat_row('assistant', chat(chat_text.value)))
        page.update()

    '''
    设置布局 添加控件
    '''
    page.add(
        Row(
            [
                ElevatedButton(
                    "导入聊天日志",
                    icon=icons.UPLOAD_FILE,
                    on_click=lambda _: pick_files_dialog.pick_files(
                        allowed_extensions=['json'],
                        allow_multiple=False,
                        dialog_title='选择聊天记录文件导入',
                        initial_directory='./chatlog'
                    ),
                ),
                ElevatedButton(
                    "保存聊天日志",
                    icon=icons.SAVE,
                    on_click=lambda _: save_file_dialog.save_file(),
                    disabled=page.web,
                ),
                ElevatedButton(
                    "打开聊天日志所在文件夹",
                    icon=icons.FOLDER_OPEN,
                    on_click=lambda _: get_directory_dialog.get_directory_path(),
                    disabled=page.web,
                ),
                settings_btn
            ],
            alignment=ft.MainAxisAlignment.END,
        ),
    )
    page.add(gpt_text)
    chat_text = ft.TextField(
        hint_text="想和chatGPT说些什么？",
        filled=True,
        expand=True,
        multiline=True)
    view = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    chat_text,
                    ft.ElevatedButton("对话", on_click=add_msg)
                ]
            ),
        ],
    )

    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(view)

    def chat(msg=None):
        try:
            print(openai.api_key)
            message = get_combined_data(chat_json_path)
            chatGPT_raw_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=message
            )
            chatGPT_response = decode_chr(
                chatGPT_raw_response.choices[0].message['content'])
            return chatGPT_response
        except openai.error.AuthenticationError as error:
            gpt_text.controls.append(
                ft.Text(f'出现如下报错\n{str(error)}\n请在设置中更新可用的apikey'))
            page.update()
        except Exception as error:
            gpt_text.controls.append(
                ft.Text(f'出现如下报错\n{str ( error )}\n请联系开发者微信B1lli_official'))
            page.update()

    '''
    版本信息
    '''
    ver_text = ft.Text('BillyGPT V3.4.0  哔哩哔哩@B1lli', size=10)
    page.add(ver_text)


if __name__ == '__main__':
    ft.app(target=ft_interface, assets_dir='assets')
