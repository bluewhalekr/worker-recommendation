# worker-recommendation

프로젝트 이름 기반의 작업자 추천 알고리즘

1. 프로젝트 유사도 측정: 동일 작업유형의 프로젝트 중 타겟 프로젝트 이름과 가장 유사한 프로젝트 탐색(TOP3)

2. 우수 작업자 추천
   - 해당 프로젝트에서 작업량이 중위값(median) 이상인 작업자들로 한정
   - 1st tier: 속도 상위25% & 정확도 상위 25%
   - 2nd tier: 속도 상위 25-50% & 정확도 상위 25%



## Set Environment with Docker

__Build Docker Image__

~~~dockerfile
docker build -t ${NAME}:${TAG} .
~~~



__Run Container__

~~~dockerfile
docker run -d -it --shm-size=${PROPER_VALUE} ${NAME}:${TAG}
~~~



## Usage

~~~python
from recommendation import get_recommendation


get_recommendation(${PROJECT_ID}) -> list([User_Id(), ...])
~~~



