import uvicorn

if __name__ == "__main__":
    uvicorn.run("smart_ward.asgi:application", reload=True)
