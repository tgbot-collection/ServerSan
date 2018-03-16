# Server Deployment
For Ubuntu 16.04

## 0. Setup bot
Talk to BotFather, get your token and add following commands:
```
start - What's this bot?
help - Help me please!
delete - Delete server info
stat - Show server info
add - Add server
```

## 1. Install dependencies
```bash
sudo apt install python python-pip python-dev git curl wget build-essential openssl
```

## 2. Install Python packages
```bash
pip install pymongo pyTelegramBotAPI flask
```

## 3. Install MongoDB
Reference: [Official Documentation](https://www.mongodb.com/download-center#community)
```bash
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 2930ADAE8CAF5059EE73BB4B58712A2291FA4AD5
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.6 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.6.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
```

Edit `/etc/mongod.conf` and make sure `bindIp` is set to`127.0.0.1`.
(Since MongoDB has no password on default, we just allow it to listen on localhost. And it's a good idea to setup firewalls.)

## 4. Download program
cd to a dir and clone the code. In this example we choose `/home`
```bash
cd /home
git clone https://github.com/BennyThink/ServerSan
```

## 5. Configure 
### (1). API
Edit `ss-agent.py` and change the API to your url. It's better to make sure it's https.

### (2). SSL certificate
We recommend using [Let's Encrypt](https://letsencrypt.org/getting-started/) to obtain an SSL certificate.
Then you should edit your path for private key and certificate in the first few lines of `weebhook.py`

## 6. Test your configuration
If you believe everything is good to go, type `python weebhook.py` and `python main.py` to check if everything is fine.

## 7. Run with systemd
As always we recommend to run the program with systemd.
### (1). webhook
Create a new file: `/lib/systemd/system/sswebhook.service`

```
[Unit]
Description=ServerSan Telegram Bot - Webhook
After=network.target network-online.target nss-lookup.target

[Service]
Restart=on-failure
Type=simple
ExecStart=/usr/bin/python /home/ServerSan/webhook.py

[Install]
WantedBy=multi-user.target
```
### (2). main program
Create a new file: `/lib/systemd/system/ssmain.service`, replace TOKEN with your bot token.
```
[Unit]
Description=ServerSan Telegram Bot - main program
After=network.target network-online.target nss-lookup.target

[Service]
Restart=on-failure
Type=simple
ExecStart=/usr/bin/python /home/ServerSan/main.py TOKEN

[Install]
WantedBy=multi-user.target
```
### (3). Reload, enable autostart and start.
```bash
systemctl daemon-reload
systemctl enable ssmain.service
systemctl start ssmain.service
systemctl enable sswebhook.service
systemctl start sswebhook.service
```

## More:
* use Nginx for upstream.
