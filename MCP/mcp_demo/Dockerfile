FROM python:3.10-slim

WORKDIR /app
RUN apt-get update && \
	apt-get install -y \
	build-essential \
	curl \
	git \
	software-properties-common \
	wget \
	&& rm -rf /var/lib/apt/lists/*

# set requests cert env
RUN wget http://certificates.intel.com/repository/certificates/IntelSHA256RootCA-Base64.crt
RUN mv IntelSHA256RootCA-Base64.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates --fresh
ENV http_proxy=http://proxy-chain.intel.com:911
ENV https_proxy=http://proxy-chain.intel.com:912
ENV no_proxy=intel.com,localhost,127.0.0.1
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

COPY . .

RUN pip3 install -r requirements.txt --proxy http://proxy-ir.intel.com:911

EXPOSE 8000

HEALTHCHECK CMD ["curl", "--fail", "http://localhost:8000/_stcore/health"]

ENTRYPOINT ["streamlit", "run", "streamlit_client.py", "--server.port=8000", "--server.address=0.0.0.0"]
