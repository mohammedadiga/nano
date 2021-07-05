FROM python:3.9

WORKDIR /app

# Install TA-lib
COPY build_helpers/* /tmp/
RUN cd /tmp && /tmp/install_ta-lib.sh && rm -r /tmp/*ta-lib*

COPY requirements.txt .
RUN pip install -r requirements.txt

ENV LD_LIBRARY_PATH /usr/local/lib

COPY /app .

CMD ["python","index.py"]