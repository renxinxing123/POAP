#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 19:41:28 2025

@author: xinxing
"""

import base64
from openai import OpenAI
import os



class Coordinator:
    def __init__(self, prompt_filepath: str):
        # 初始化 OpenAI 客户端
        self.client = OpenAI()
        # 加载 operator 提示信息
        self.operator_prompt = self.load_operator_prompt(prompt_filepath)
        # 初始化对话历史，将系统提示信息作为第一条消息
        self.conversation_history = [{"role": "system", "content": self.operator_prompt}]

    @staticmethod
    def load_operator_prompt(filepath: str) -> str:
        """从指定文件中加载 operator 提示信息。"""
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            print(f"加载系统消息失败：{e}")
            return "默认系统提示信息"

    @staticmethod
    def encode_image(image_path: str) -> str:
        """将图片转为 Base64 编码字符串。"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            print(f"图片读取失败：{e}")
            return None

    def run(self, user_text: str, send_image: bool = False, image_path: str = None) -> str:
        """
        处理用户输入的文本和可选图片，并返回 LLM 回复内容。
        
        参数:
            user_text: 用户输入的文本消息。
            send_image: 是否需要发送图片（默认为 False）。
            image_path: 如果 send_image 为 True，此处指定图片路径。
        """
        # 构造消息内容
        if send_image and image_path:
            base64_image = self.encode_image(image_path)
            if base64_image:
                message_content = [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high",
                        },
                    },
                ]
            else:
                print("图片处理失败，发送纯文本消息。")
                message_content = [{"type": "text", "text": user_text}]
        else:
            message_content = [{"type": "text", "text": user_text}]
        
        # 将用户消息添加到对话历史中
        self.conversation_history.append({"role": "user", "content": message_content})
        
        try:
            # 调用 LLM 接口，传入完整的对话历史
            response = self.client.chat.completions.create(
                model="chatgpt-4o-latest",
                messages=self.conversation_history,
            )
            reply_content = response.choices[0].message.content
            # 将回复添加到对话历史
            self.conversation_history.append({"role": "assistant", "content": reply_content})
            return reply_content
        except Exception as e:
            return f"调用接口失败：{e}"
        
class SentimentAnalysistAgent:
    def __init__(self, prompt_filepath: str):
        # 初始化 OpenAI 客户端
        self.client = OpenAI()
        # 加载系统提示信息并初始化对话历史
        sentiment_prompt = self.load_system_prompt(prompt_filepath)
        self.conversation_history = [{"role": "system", "content": sentiment_prompt}]

    @staticmethod
    def load_system_prompt(filepath: str) -> str:
        """从指定文件中加载系统提示信息。"""
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            print(f"加载系统消息失败：{e}")
            return "默认系统提示信息"

    def run(self, query: str) -> str:
        """
        处理用户输入的 query，更新对话历史，并返回模型回复。
        当 query 为 'exit' 时，直接返回退出消息。
        """
        if query.lower() == "exit":
            return "退出 Sentiment_analysist agent."
        
        self.conversation_history.append({"role": "user", "content": query})

        try:
            response = self.client.chat.completions.create(
                model="chatgpt-4o-latest",
                messages=self.conversation_history,
            )
            reply_content = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": reply_content})
            return reply_content
        except Exception as e:
            return f"调用接口失败：{e}"
        
class TopicModellingAgent:
    def __init__(self, prompt_filepath: str):
        # 初始化 OpenAI 客户端
        self.client = OpenAI()
        # 加载系统提示信息并初始化对话历史
        topic_prompt = self.load_system_prompt(prompt_filepath)
        self.conversation_history = [{"role": "system", "content": topic_prompt}]

    @staticmethod
    def load_system_prompt(filepath: str) -> str:
        """从指定文件中加载系统提示信息。"""
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            print(f"加载系统消息失败：{e}")
            return "默认系统提示信息"

    def run(self, query: str) -> str:
        """
        处理用户输入的 query，更新对话历史，并返回模型回复。
        当 query 为 'exit' 时，直接返回退出消息。
        """
        if query.lower() == "exit":
            return "退出 Topic_modelling agent."
        
        self.conversation_history.append({"role": "user", "content": query})

        try:
            response = self.client.chat.completions.create(
                model="chatgpt-4o-latest",
                #model = "o3_mini",
                messages=self.conversation_history,
            )
            reply_content = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": reply_content})
            return reply_content
        except Exception as e:
            return f"调用接口失败：{e}"
        
class Summarizer:
    def __init__(self, prompt_filepath: str):
        # 初始化 OpenAI 客户端
        self.client = OpenAI()
        # 加载系统提示信息并初始化对话历史
        system_message = self.load_system_message(prompt_filepath)
        self.conversation_history = [{"role": "system", "content": system_message}]

    @staticmethod
    def load_system_message(filepath: str) -> str:
        """从指定文件中加载系统提示信息。"""
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            print(f"加载系统消息失败：{e}")
            return "默认系统提示信息"

    def run(self, query: str) -> str:
        """
        处理用户输入的 query，更新对话历史，并返回模型回复。
        当 query 为 'exit' 时，直接返回退出消息。
        """
        if query.lower() == "exit":
            return "退出 Summarizer agent."
        
        self.conversation_history.append({"role": "user", "content": query})
        try:
            response = self.client.chat.completions.create(
                model="chatgpt-4o-latest",
                messages=self.conversation_history,
            )
            reply_content = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": reply_content})
            return reply_content
        except Exception as e:
            return f"调用接口失败：{e}"
