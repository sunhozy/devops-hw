from troposphere import Base64, Join, Output, Ref
from troposphere.ec2 import Instance, SecurityGroup, SecurityGroupRule
from troposphere import Template

# Template 정의
t = Template()

# 변수 정의
ApplicationPort = "8080"
PublicCidrIp = "0.0.0.0/0"
AnsiblePullCmd = "ansible-pull -U https://github.com/example/repo.git"

# KeyPair
t.add_parameter(Parameter(
    "KeyPair",
    Description="Name of an existing EC2 KeyPair to SSH",
    Type="AWS::EC2::KeyPair::KeyName",
    ConstraintDescription="must be the name of an existing EC2 KeyPair.",
))

# SecurityGroup
t.add_resource(SecurityGroup(
    "SecurityGroup",
    GroupDescription="Allow SSH and TCP/{} access".format(ApplicationPort),
    SecurityGroupIngress=[
        SecurityGroupRule(
            IpProtocol="tcp",
            FromPort="22",
            ToPort="22",
            CidrIp=PublicCidrIp,
        ),
        SecurityGroupRule(
            IpProtocol="tcp",
            FromPort=ApplicationPort,
            ToPort=ApplicationPort,
            CidrIp="0.0.0.0/0",
        ),
    ],
))

# UserData (스크립트)
ud = Base64(Join('\n', [
    "#!/bin/bash",
    "yum install --enablerepo=epel -y git",
    "yum install --enablerepo=epel -y ansible",
    AnsiblePullCmd,
    "echo '*/10 * * * * {}' > /etc/cron.d/ansible-pull".format(AnsiblePullCmd)
]))

# EC2 Instance
t.add_resource(Instance(
    "instance",
    ImageId="ami-cfe4b2b0",  # 실제 사용하려는 리전의 유효한 AMI ID로 변경
    InstanceType="t2.micro",
    SecurityGroups=[Ref("SecurityGroup")],
    KeyName=Ref("KeyPair"),
    UserData=ud,
))

# Outputs
t.add_output(Output(
    "InstancePublicIp",
    Description="Public IP of our instance.",
    Value=GetAtt("instance", "PublicIp"),
))

t.add_output(Output(
    "WebUrl",
    Description="Application endpoint",
    Value=Join("", [
        "http://", GetAtt("instance", "PublicDnsName"),
        ":", ApplicationPort
    ])),
)

# CloudFormation JSON 출력
print(t.to_json())

