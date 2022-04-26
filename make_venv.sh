#!/bin/bash
if ! python3 -V &>/dev/null; then
        echo "python3未安装,请安装python3"
        exit 1
    else
        echo "python已安装"
        if python3 -c "import pip" >/dev/null 2>&1; then
            echo "pip已安装"
        else
            echo "开始安装pip"
            sudo apt install python3-pip -y
        fi
        python3 -m pip install --user virtualenv
fi

python3 -m virtualenv venv
source venv/bin/activate
pip install -r requirements.txt

sed -i "s@PWD_PATH@${PWD}@g" gunicorn_supervisor.conf
sed -i "s@VENV_PATH@${PWD}/venv@g" gunicorn_supervisor.conf

sudo cp gunicorn_supervisor.conf /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo supervisorctl update
