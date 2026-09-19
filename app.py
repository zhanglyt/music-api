#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import time
from urllib.parse import quote

app = Flask(__name__)
CORS(app)

QQ_SEARCH_URL = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp"
QQ_VKEY_URL = "https://u.y.qq.com/cgi-bin/musicu.fcg"
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://y.qq.com"}

@app.route("/")
def index():
    return jsonify({"service": "车载音乐解析服务", "version": "1.1"})

@app.route("/api/search")
def search():
    keyword = request.args.get("keyword", "")
    if not keyword:
        return jsonify({"error": "keyword不能为空"}), 400
    
    params = {"w": keyword, "format": "json", "p": 1, "n": 30, "cr": 1, "g_tk": 5381}
    try:
        resp = requests.get(QQ_SEARCH_URL, params=params, headers=HEADERS, timeout=10)
        resp.encoding = 'utf-8'
        data = resp.json()
        songs = data.get("data", {}).get("song", {}).get("list", [])
        result = []
        for s in songs:
            songmid = s.get("songmid", "")
            singer = ",".join([x.get("name", "") for x in s.get("singer", [])])
            albummid = s.get("albummid", "")
            pic_url = f"https://y.gtimg.cn/music/photo_new/T002R300x300M000{albummid}.jpg" if albummid else ""
            result.append({
                "id": songmid, "songmid": songmid,
                "name": s.get("songname", ""), "title": s.get("songname", ""),
                "artist": singer, "singer": singer,
                "album": s.get("albumname", ""),
                "pic": pic_url, "cover": pic_url,
                "duration": s.get("interval", 0)
            })
        return jsonify({"success": True, "total": len(result), "data": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/url")
def get_url():
    songmid = request.args.get("songmid", "")
    if not songmid:
        return jsonify({"error": "songmid不能为空"}), 400
    
    try:
        post_data = {"req_1": {"module": "vkey.GetVkeyServer", "method": "CgiGetVkey",
            "param": {"guid": str(int(time.time())), "songmid": [songmid], "songtype": [0],
                      "uin": "0", "loginflag": 1, "platform": "20"}}}
        resp = requests.post(QQ_VKEY_URL, json=post_data, headers=HEADERS, timeout=10)
        data = resp.json()
        req1_data = data.get("req_1", {}).get("data", {})
        midurlinfo = req1_data.get("midurlinfo", [])
        sip = req1_data.get("sip", [])
        if midurlinfo and sip and midurlinfo[0].get("purl"):
            return jsonify({"success": True, "url": sip[0] + midurlinfo[0]["purl"]})
        return jsonify({"success": False, "error": "无法获取播放地址"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/lyric")
def get_lyric():
    songmid = request.args.get("songmid", "")
    if not songmid:
        return jsonify({"error": "songmid不能为空"}), 400
    try:
        url = "https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg"
        params = {"songmid": songmid, "g_tk": 5381, "format": "json", "inCharset": "utf8", "outCharset": "utf-8"}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = resp.json()
        return jsonify({"success": True, "lyric": data.get("lyric", "")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
