from flask import Flask, request, redirect, url_for, render_template_string
import os
import time
import requests
import threading

app = Flask(__name__)

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
}

# Global variables
stop_flag = False
status = {
    'total_sent': 0,
    'current_message': '',
    'total_messages': 0
}

def send_messages(token_type, access_token, thread_id, hater_name, time_interval, messages, tokens):
    global stop_flag, status
    post_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
    
    status['total_messages'] = len(messages)
    msg_index = 0
    while not stop_flag:
        message = messages[msg_index % len(messages)]
        token = access_token if token_type == 'single' else tokens[msg_index % len(tokens)]

        data = {'access_token': token, 'message': f"{hater_name} {message}"}
        response = requests.post(post_url, json=data, headers=headers)

        status['current_message'] = message
        if response.ok:
            status['total_sent'] += 1
            print(f"[SUCCESS] Sent: {message}")
        else:
            print(f"[FAILURE] Failed to send: {message} | {response.text}")

        msg_index += 1
        time.sleep(time_interval)


@app.route('/')
def index():
    return '''
    <h2>Auto Message Sender</h2>
    <form action="/" method="post" enctype="multipart/form-data">
      Token Type: 
      <select name="tokenType">
        <option value="single">Single Token</option>
        <option value="multi">Multi Token</option>
      </select><br><br>
      Access Token: <input type="text" name="accessToken"><br><br>
      Thread ID: <input type="text" name="threadId" required><br><br>
      Hater Name: <input type="text" name="kidx" required><br><br>
      Message File: <input type="file" name="txtFile" required><br><br>
      Token File (for multi): <input type="file" name="tokenFile"><br><br>
      Speed (seconds): <input type="number" name="time" required><br><br>
      <button type="submit">Start Sending</button>
    </form>
    <br>
    <form action="/stop" method="post">
      <button type="submit">Stop Sending</button>
    </form>
    <br>
    <a href="/status" target="_blank">View Live Status</a>
    '''

@app.route('/', methods=['POST'])
def process_form():
    global stop_flag
    stop_flag = False

    token_type = request.form.get('tokenType')
    access_token = request.form.get('accessToken')
    thread_id = request.form.get('threadId')
    hater_name = request.form.get('kidx')
    time_interval = int(request.form.get('time'))
    
    txt_file = request.files['txtFile']
    messages = txt_file.read().decode().splitlines()
    
    tokens = []
    if token_type == 'multi':
        token_file = request.files.get('tokenFile')
        if token_file:
            tokens = token_file.read().decode().splitlines()

    threading.Thread(target=send_messages, args=(token_type, access_token, thread_id, hater_name, time_interval, messages, tokens), daemon=True).start()

    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop_sending():
    global stop_flag
    stop_flag = True
    return redirect(url_for('index'))

@app.route('/status')
def status_page():
    global status
    # Simple HTML template for live status
    template = '''
    <h2>Live Message Status</h2>
    <p><b>Total Messages:</b> {{ total_messages }}</p>
    <p><b>Total Sent:</b> {{ total_sent }}</p>
    <p><b>Current Message:</b> {{ current_message }}</p>
    <meta http-equiv="refresh" content="2">
    '''
    return render_template_string(template, total_messages=status['total_messages'], total_sent=status['total_sent'], current_message=status['current_message'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
