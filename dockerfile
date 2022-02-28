# 베이스 이미지 지정
FROM ubuntu:latest

LABEL purpose = 'eimmo worker-recommendation system' \
      version = '1.0' \
      description = 'worker-recommendation based on projects title similarity'

RUN apt-get update -y \
    && apt-get install -y wget \
    && apt-get install -y automake1.11 \
    && apt-get install -y python3-pip \
    && apt-get clean \
    && apt-get autoremove -y \
    && rm -rfv /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /home/worker-recommendation/

# 패키지 복사
COPY ./ /home/worker-recommendation

# mecab-ko 설치
RUN mkdir mecab \
    && cd mecab \
    && wget https://bitbucket.org/eunjeon/mecab-ko/downloads/mecab-0.996-ko-0.9.2.tar.gz \
    && tar zxfv mecab-0.996-ko-0.9.2.tar.gz \
    && cd mecab-0.996-ko-0.9.2 \
    && ./configure \
    && make \
    && make check \
    && su \
    && make install

# mecab-ko-dic 설치
RUN ldconfig \
    && cd mecab \
    && wget https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/mecab-ko-dic-2.1.1-20180720.tar.gz \
    && tar zxfv mecab-ko-dic-2.1.1-20180720.tar.gz \
    && rm -rf *.tar.gz \
    && cd mecab-ko-dic-2.1.1-20180720 \
    && ./configure \
    && make \
    && su \
    && make install \
    && cd user-dic \
    && rm -rf ./nnp.csv

# 사용자사전 추가
COPY ./nnp.csv /home/worker-recommendation/mecab/mecab-ko-dic-2.1.1-20180720/user-dic/ 

RUN cd ./mecab/mecab-ko-dic-2.1.1-20180720 \
    && ./tools/add-userdic.sh \
    && make install \
    && rm -rf ./user-nnp.csv

# 사용자사전 우선순위 적용
COPY ./user-nnp.csv /home/worker-recommendation/mecab/mecab-ko-dic-2.1.1-20180720/

RUN rm -rf *.csv \
    && cd ./mecab/mecab-ko-dic-2.1.1-20180720 \
    && make clean \
    && make install

# Requirements 설치
RUN pip3 install -r requirements.txt