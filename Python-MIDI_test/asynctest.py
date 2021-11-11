import asyncio
import time

async def start_time(src):
    await asyncio.sleep(src)
    print("START!!!")

async def main_process(span):
    idx = 1
    while True:
        await asyncio.sleep(span)
        num_active_tasks = len([ task for task in asyncio.Task.all_tasks(loop) if not task.done()])
        if num_active_tasks == 1:
            break
        print("[run:{}]{}秒経過".format(num_active_tasks, idx * span))
        idx += 1


async def end_time(src):
    await asyncio.sleep(src)
    print("END!!!")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(
                start_time(10),
                main_process(1),
                end_time(20)
            )
        )
    finally:
        loop.close()
