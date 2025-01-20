import pulumi
import pulumi_aws as aws
import json

# Configuration
config = pulumi.Config()
app_port = 5000
desired_count = 1
db_password = config.require_secret('db_password')
db_username = config.require('db_username')
db_name = config.require('db_name')
db_port = config.require('db_port')

# Create VPC
vpc = aws.ec2.Vpc("precis-dev",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": "precis-dev"
    })

# Create public subnets
public_subnet_1 = aws.ec2.Subnet("precis-dev-1",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-east-1a",
    map_public_ip_on_launch=True,
    tags={
        "Name": "precis-dev-1"
    })

public_subnet_2 = aws.ec2.Subnet("precis-dev-2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="us-east-1b",
    map_public_ip_on_launch=True,
    tags={
        "Name": "precis-dev-2"
    })

# Create Internet Gateway
igw = aws.ec2.InternetGateway("precis-dev-igw",
    vpc_id=vpc.id,
    tags={
        "Name": "precis-dev-igw"
    })

# Create route table
route_table = aws.ec2.RouteTable("precis-dev-route-table",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        )
    ],
    tags={
        "Name": "precis-dev-route-table"
    })

# Associate route table with subnets
rta1 = aws.ec2.RouteTableAssociation("rta-1",
    subnet_id=public_subnet_1.id,
    route_table_id=route_table.id)

rta2 = aws.ec2.RouteTableAssociation("rta-2",
    subnet_id=public_subnet_2.id,
    route_table_id=route_table.id)

# Create ECS Cluster
cluster = aws.ecs.Cluster("precis-dev-cluster")

# Create ECR Repository
repo = aws.ecr.Repository("precis-dev-repo",
    image_tag_mutability="MUTABLE")

# Get registry info
registry = repo.repository_url.apply(
    lambda url: url.split("/")[0]
)

# Create Docker image
image = docker.Image("app-image",
    build=docker.DockerBuildArgs(
        context="../",  # Path to the directory containing Dockerfile
        dockerfile="../Dockerfile",
    ),
    image_name=repo.repository_url.apply(lambda url: f"{url}:latest"),
    registry=docker.RegistryArgs(
        server=registry,
        username="AWS",
        password=pulumi.Output.secret(aws.get_caller_identity().apply(
            lambda id: aws.ecr.get_authorization_token(registry_id=id.account_id)
        ).password)
    )
)

# Create IAM role for ECS task execution
task_execution_role = aws.iam.Role("ecsTaskExecutionRole",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Effect": "Allow",
            "Sid": ""
        }]
    }))

# Attach policy to role
aws.iam.RolePolicyAttachment("ecsTaskExecutionRolePolicy",
    role=task_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy")

# Create Application Load Balancer
alb = aws.lb.LoadBalancer("precis-dev-lb",
    internal=False,
    load_balancer_type="application",
    security_groups=[],  # We'll add this later
    subnets=[public_subnet_1.id, public_subnet_2.id])

# Create ALB target group
target_group = aws.lb.TargetGroup("precis-dev-tg",
    port=app_port,
    protocol="HTTP",
    target_type="ip",
    vpc_id=vpc.id,
    health_check={
        "enabled": True,
        "path": "/healthz",
        "interval": 30,
        "timeout": 5,
        "healthy_threshold": 2,
        "unhealthy_threshold": 2
    })

# Create ALB listener
listener = aws.lb.Listener("precis-dev-listener",
    load_balancer_arn=alb.arn,
    port=80,
    default_actions=[{
        "type": "forward",
        "target_group_arn": target_group.arn
    }])

# Create security group for ALB
alb_security_group = aws.ec2.SecurityGroup("alb-sg",
    vpc_id=vpc.id,
    description="Security group for ALB",
    ingress=[{
        "protocol": "tcp",
        "from_port": 80,
        "to_port": 80,
        "cidr_blocks": ["0.0.0.0/0"],
    }],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
    }])

# Update ALB security groups
alb.security_groups = [alb_security_group.id]

# Create security group for ECS tasks
task_security_group = aws.ec2.SecurityGroup("task-sg",
    vpc_id=vpc.id,
    description="Security group for ECS tasks",
    ingress=[{
        "protocol": "tcp",
        "from_port": app_port,
        "to_port": app_port,
        "security_groups": [alb_security_group.id],
    }],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
    }])

# Create security group for RDS
db_security_group = aws.ec2.SecurityGroup("db-sg",
    vpc_id=vpc.id,
    description="Security group for RDS PostgreSQL",
    ingress=[
        # Allow access from ECS tasks
        {
            "protocol": "tcp",
            "from_port": 5432,
            "to_port": 5432,
            "security_groups": [task_security_group.id],
        },
        # Allow external access
        {
            "protocol": "tcp",
            "from_port": 5432,
            "to_port": 5432,
            "cidr_blocks": ["0.0.0.0/0"],  # Allow connections from anywhere
        }
    ],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
    }],
    tags={
        "Name": "db-sg"
    })

# Create DB subnet group
db_subnet_group = aws.rds.SubnetGroup("db-subnet-group",
    subnet_ids=[public_subnet_1.id, public_subnet_2.id],
    tags={
        "Name": "db-subnet-group"
    })

# Create RDS instance
db_instance = aws.rds.Instance("precis-dev-db",
    engine="postgres",
    engine_version="14",
    instance_class="db.t3.micro",
    allocated_storage=20,
    storage_type="gp2",
    username=db_username,
    name=db_name,
    password=db_password,
    vpc_security_group_ids=[db_security_group.id],
    db_subnet_group_name=db_subnet_group.name,
    publicly_accessible=True,
    skip_final_snapshot=True,
    tags={
        "Name": "precis-dev-db"
    })

pulumi.export("db_instance_endpoint", db_instance.endpoint)

# Database URL
db_url = pulumi.Output.concat(
    "postgresql://", db_username, ":", db_password, "@",
    db_instance.endpoint, "/", db_name
)

# Create ECS Task Definition
task_definition = aws.ecs.TaskDefinition("precis-dev-task",
    family="flask-app",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=task_execution_role.arn,
    container_definitions=json.dumps([{
        "name": "flask-app",
        "image": repo.repository_url,
        "portMappings": [{
            "containerPort": app_port,
            "hostPort": app_port,
            "protocol": "tcp"
        }],
		"environment": [
            {
                "name": "DATABASE_URL",
                "value": db_url
            },
            {
                "name": "FLASK_ENV",
                "value": "production"
            }
        ],
        "essential": True,
    }]))

# Create ECS Service
service = aws.ecs.Service("precis-dev-service",
    cluster=cluster.arn,
    desired_count=desired_count,
    launch_type="FARGATE",
    task_definition=task_definition.arn,
    network_configuration={
        "assign_public_ip": True,
        "subnets": [public_subnet_1.id, public_subnet_2.id],
        "security_groups": [task_security_group.id],
    },
    load_balancers=[{
        "target_group_arn": target_group.arn,
        "container_name": "flask-app",
        "container_port": app_port,
    }],
    opts=pulumi.ResourceOptions(depends_on=[listener]))

# Export the load balancer URL
pulumi.export("url", alb.dns_name)

# Export the database url
pulumi.export("db_url", db_url)