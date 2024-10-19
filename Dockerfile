# 使用官方 Python 基礎鏡像
FROM python:3.9

# 設置工作目錄
WORKDIR /usr/src/app

# 複製需求文件並安裝 Python 依賴
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有應用程式代碼到工作目錄
COPY . .

# 指定啟動命令
CMD ["python", "main.py"]
