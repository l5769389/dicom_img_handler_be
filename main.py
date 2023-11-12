import asyncio
import json
import multiprocessing
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket

from ws.ws_recv_msg_op import ws_recv_msg_op
from config.config import ip, port
from ws.ws_manage import manager
from fastapi.staticfiles import StaticFiles
import uuid

connected_clients = {}
pause_events_dic = {}
pause_event = None
# 用来处理3d出图的时候需要通知websocket进程新建的图像处理对象的问题。
parent_conn, child_conn = multiprocessing.Pipe()
ws_send_msg_queue = multiprocessing.Queue(500)
ws_recv_msg_queue = multiprocessing.Queue(100)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 开发静态目录
app.mount('/static', StaticFiles(directory='static'), name='static')


@app.get("/3d")
def get_vti_file():
    ws_recv_msg_queue.put(json.dumps({
        'opType': 'get_3d',
        'type': '3d'
    }))
    ans = parent_conn.recv()
    return {
        "code": 1 if ans else 0
    }


@app.get("/play")
def play():
    pass


@app.get("/pause")
def pause():
    global pause_event
    pause_event.set()
    return {
        "code": 1
    }


@app.get("/stop")
def stop():
    pass


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    print('ws连接成功')
    await manager.connect(websocket)
    await handle_websocket(websocket)


async def handle_websocket(websocket: WebSocket):
    global pause_events_dic
    global pause_event
    client_id = uuid.uuid4().hex
    connected_clients[client_id] = websocket

    pause_event = multiprocessing.Event()
    pause_events_dic[client_id] = pause_event
    recv_op = ws_recv_msg_op(ws_send_msg_queue, ws_recv_msg_queue, pause_event, child_conn)
    recv_op.start()
    try:
        while True:
            while not ws_send_msg_queue.empty():
                msg = ws_send_msg_queue.get()
                await websocket.send_text(msg)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                ws_recv_msg_queue.put(data)
            except asyncio.TimeoutError:
                pass
    except Exception as e:
        print(e)
        manager.disconnect(websocket)
        del connected_clients[client_id]
        del pause_events_dic[client_id]
        recv_op.terminate()


def run_server():
    uvicorn.run(app, host=ip, port=port)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    # img_op_pool = multiprocessing.Pool(processes=4)
    run_server()
