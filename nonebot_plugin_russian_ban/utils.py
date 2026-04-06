import json
from pathlib import Path
from pydantic import BaseModel
from typing import Dict, List, Union
from nonebot import require
from nonebot.log import logger

require("nonebot_plugin_localstore")

import nonebot_plugin_localstore as store

zh_number = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

DATAFILE = store.get_plugin_data_file("russian_ban.json")


def to_int(N) -> int | None:
    try:
        result = int(N)
    except ValueError:
        result = zh_number.get(N)
    return result


def format_timedelta(seconds: int) -> str:
    days = seconds // 86400
    seconds -= days * 86400
    hours = seconds // 3600
    seconds -= hours * 3600
    minutes = seconds // 60
    seconds -= minutes * 60
    result = []
    if days > 0:
        result.append(f"{days} 天")
    if hours > 0:
        result.append(f"{hours} 小时")
    if minutes > 0:
        result.append(f"{minutes} 分钟")
    if seconds > 0:
        result.append(f"{seconds} 秒")
    return "".join(result)


class NapcatAPI(BaseModel):
    uin: str
    nick: str
    shutUpTime: int

class OnebotAPI(BaseModel):
    user_id: int
    nickname: str
    shut_up_timestamp: int

BanList = List[Union[NapcatAPI, OnebotAPI]]

class Ban:
    @staticmethod
    def banlist(data: List[dict]) -> BanList:
        result = []
        for item in data:
            if 'uin' in item:
                result.append(NapcatAPI(**item))
            elif 'user_id' in item:
                result.append(OnebotAPI(**item))
        return result
    
    @staticmethod
    def banlist_to_list(data: List[dict]) -> BanList:
        result = []
        for item in data:
            if 'uin' in item:
                result.append(NapcatAPI(**item).__dict__)
            elif 'user_id' in item:
                result.append(OnebotAPI(**item).__dict__)
        return result


class BanGameState(BaseModel):
    switch: bool = False
    star: int = 0
    st: int = 0
    hell_switch: bool = False
    hell_duration: int = 0


class FileMange:

    data_path: Path = DATAFILE

    states: dict[int, BanGameState] = {} 

    @classmethod
    async def ensure(cls):
        try:
            cls.data_path.parent.mkdir(parents=True, exist_ok=True)
            if not cls.data_path.exists():
                with open(cls.data_path, "w", encoding="utf-8") as f:
                    json.dump(cls.states, f, indent=4, ensure_ascii=False)
        except FileNotFoundError as e:
            logger.error(f"创建数据文件失败：{cls.data_path}，{e}")


    @classmethod
    async def load(cls):
        try:
            await cls.ensure()
            with open(cls.data_path, encoding="utf-8") as f:
                data = json.load(f)
            if data:
                for k, v in data.items():
                    cls.states[int(k)] = BanGameState(**v)
        except json.JSONDecodeError as e:
            logger.error(f"加载json文件失败，json格式出错：{e}")
            with open(cls.data_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    with open(cls.data_path, "w", encoding="utf-8") as f2:
                        json.dump({}, f2)
                    logger.warning(f"文件内容为空，已重置: {cls.data_path}")
        except Exception as e:
            logger.error(f"load函数报错{e}，加载数据：\n{data}\n{cls.states}")


    @classmethod
    async def save(cls):
        try:
            await cls.ensure()
            save_data = {}
            for k, v in cls.states.items():
                if k:
                    save_data[str(k)] = v.model_dump(include={"switch"})
            with open(cls.data_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"save函数报错{e}")