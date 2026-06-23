import asyncio
import httpx

async def test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Upload
        files = {'file': ('test.csv', b"A,B\nfoo,1\n ,2\nbar,3\n,4")}
        res = await client.post("http://localhost:8000/api/upload", files=files)
        sid = res.json()["session_id"]
        print("Session:", sid)
        
        # 2. Apply cleaning (Empty Cells -> Remove Rows)
        req = {"issue": "Empty Cells", "columns": ["all"], "method": "Remove Rows"}
        res = await client.post(f"http://localhost:8000/api/clean/{sid}/apply", json=req)
        print("Apply:", res.status_code)
        
        # 3. Get table
        res = await client.get(f"http://localhost:8000/api/table/{sid}?dataset=cleaned&limit=10000")
        print("Table:", res.status_code)
        if res.status_code == 500:
            print(res.text)

if __name__ == '__main__':
    asyncio.run(test())
