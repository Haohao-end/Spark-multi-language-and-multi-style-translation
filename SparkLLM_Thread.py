# SparkLLM_Thread.py
import _thread as thread
import base64
import hashlib
import hmac
import json
import time
import logging
from urllib.parse import urlparse, urlencode
from datetime import datetime
from wsgiref.handlers import format_date_time
import websocket
from typing import List, Dict

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SparkLLMClient:
    def __init__(self, appid: str, api_key: str, api_secret: str, gpt_url: str):
        self.APPID = appid
        self.APIKey = api_key
        self.APISecret = api_secret
        self.host = urlparse(gpt_url).netloc
        self.path = urlparse(gpt_url).path
        self.gpt_url = gpt_url
        self.answer = ''
        self.tokens = 0

    def create_url(self) -> str:
        try:
            now = datetime.now()
            date = format_date_time(time.mktime(now.timetuple()))
            signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.path} HTTP/1.1"
            
            signature_sha = hmac.new(
                self.APISecret.encode('utf-8'),
                signature_origin.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            
            signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')
            authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
            authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
            
            params = {"authorization": authorization, "date": date, "host": self.host}
            return self.gpt_url + '?' + urlencode(params)
        except Exception as e:
            logger.error(f"URL creation failed: {str(e)}")
            raise

    def on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logger.info("WebSocket connection closed")

    def on_open(self, ws):
        thread.start_new_thread(self.run, (ws,))

    def run(self, ws, *args):
        try:
            data = json.dumps(self.gen_params(ws.appid, ws.question, ws.uid, ws.chat_id))
            ws.send(data)
        except Exception as e:
            logger.error(f"Failed to send data: {str(e)}")

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            code = data['header']['code']
            
            if code != 0:
                logger.error(f"Request failed: {code}, {data}")
                ws.close()
                return
            
            choices = data["payload"]["choices"]
            content = choices["text"][0]["content"]
            self.answer += content
            
            if choices["status"] == 2:
                self.tokens = data["payload"]["usage"]
                ws.close()
        except Exception as e:
            logger.error(f"Message processing failed: {str(e)}")

    @staticmethod
    def gen_params(appid: str, question: List[Dict], uid: str, chat_id: str) -> Dict:
        return {
            "header": {"app_id": appid, "uid": uid},
            "parameter": {
                "chat": {
                    "domain": "4.0Ultra",
                    "temperature": 0.8,
                    "top_k": 6,
                    "max_tokens": 4096,
                    "auditing": "default",
                    "stream": True,
                    "chat_id": chat_id
                }
            },
            "payload": {"message": {"text": question}}
        }

    def query(self, uid: str, chat_id: str, question: List[Dict]) -> tuple:
        ws_url = self.create_url()
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        
        ws.appid = self.APPID
        ws.uid = uid
        ws.chat_id = chat_id
        ws.question = question
        
        self.answer = ''
        start_time = time.time()
        ws.run_forever()
        
        return self.answer, self.tokens, time.time() - start_time

def main(uid: str, chat_id: str, appid: str, api_key: str, api_secret: str, 
         gpt_url: str, question: List[Dict]) -> tuple:
    client = SparkLLMClient(appid, api_key, api_secret, gpt_url)
    try:
        result, tokens, duration = client.query(uid, chat_id, question)
        logger.info(f"Query completed in {duration:.2f}s, tokens used: {tokens}")
        return result
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        return f"Error: {str(e)}"
