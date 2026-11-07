from fastapi import FastAPI,status,HTTPException,Header,Depends
from sqlmodel import SQLModel,Field,create_engine,Session,select
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional
engine = create_engine("sqlite:///./classInfo.db", echo=True)
def get_session():
    with Session(engine) as session:
        yield session
class Student(SQLModel,table=True):
    id: Optional[int] = Field(default=None, primary_key=True) #数据库id
    sid : int = Field(unique=True,index=True)
    passwd : str
    name : str
    age : int
    sex : str
    role : str

class StudentOut(SQLModel):  #用于查询时返回不出password
    id : int
    sid : int
    name : str
    age : int
    sex : str
    role: str
#class AddStudent(SQLModel):
 #   msg : str
  #  student : StudentOut
class StudentModify(SQLModel):
    name : Optional[str]=None
    passwd : Optional[str]=None
    age : Optional[int]=None
    sex : Optional[str]=None
    role : Optional[str]=None


def require_admin(x_sid:int=Header(None),session:Session=Depends(get_session)):
    if not x_sid:
        raise HTTPException(status_code=401,detail="未登录，请在Header中提供学号")
    student=session.exec(select(Student).where(Student.sid==x_sid)).first()
    if not student:
        raise HTTPException(status_code=404, detail="未找到用户")
    if student.role=="admin":
        return student
    else:
        raise HTTPException(status_code=403,detail="非管理员")
@asynccontextmanager
async def lifespan(app : FastAPI):
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        admin = session.exec(select(Student).where(Student.role == "admin")).first()
        if not admin:
            init_admin = Student(sid=2025001, passwd="1234", name="张三", age=18, sex="男", role="admin")
            session.add(init_admin)
            session.commit()
            session.refresh(init_admin)
    yield
app=FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_credentials=True,allow_headers=["*"]) #跨域处理

@app.post("/login") #登录
def login(sid:int,password:str,session:Session=Depends(get_session)):
    student=session.exec(select(Student).where(Student.sid==sid)).first()
    if not student:
        raise HTTPException(404,detail="学号不存在")

    if student.passwd==password:
        return {"msg":"登陆成功"}
    else:
        raise HTTPException(status_code=404,detail="密码错误")

@app.get("/students",response_model=list[StudentOut]) #全量查
def read_students(session:Session=Depends(get_session),skip:int=0,limit:int=10):
    students=session.exec(select(Student).offset(skip).limit(limit)).all()
    return students
@app.get("/students/{stu_id}",response_model=StudentOut)
def read_student(stu_id:int,session:Session=Depends(get_session)):
    stu=session.exec(select(Student).where(Student.sid==stu_id)).first()
    if not stu:
        raise HTTPException(status_code=404,detail="未找到当前学号学生")
    return stu
@app.post("/students",response_model=StudentOut,status_code=status.HTTP_201_CREATED)
def add_student(student:Student,admin : Student = Depends(require_admin),session:Session=Depends(get_session)):
    st=session.exec(select(Student).where(Student.sid==student.sid)).first()
    if st:
        raise HTTPException(409,detail="学号重复!")
    session.add(student)
    session.commit()
    session.refresh(student)
    return student

@app.patch("/students/{stu_id}")
def modify_student(stu_id:int,update_student:StudentModify,admin : Student = Depends(require_admin),session:Session=Depends(get_session)):
    student=session.exec(select(Student).where(Student.sid==stu_id)).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生学号不存在!")
    student_dict=update_student.model_dump(exclude_unset=True)
    for key,value in student_dict.items():
        setattr(student,key,value)
    session.add(student)
    session.commit()
    session.refresh(student)
    return {"msg":"修改成功"}

@app.delete("/students/{stu_id}")
def delete_student(stu_id : int,admin : Student = Depends(require_admin),session:Session=Depends(get_session)):
    student=session.exec(select(Student).where(Student.sid==stu_id)).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生学号不存在")
    session.delete(student)
    session.commit()
    return {"msg":"删除成功"}

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app,host="127.0.0.1",port=8080)










