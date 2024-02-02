# Specify the provider (AWS)
provider "aws" {
  region = "us-east-2" # Update with your desired region
}

# Creating a IAM user to access the resources
resource "aws_iam_user" "user" {
  name = "onlibrary-user" # Replace with your desired username
}

# Create a S3 Bucket
resource "aws_s3_bucket" "bucket" {
  bucket = "mhsw-onlibrary" # Replace with your desired bucket name
}

# Setting bucket controls
resource "aws_s3_bucket_ownership_controls" "bucket" {
  bucket = aws_s3_bucket.bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# Allowing public ACLs for the bucket
resource "aws_s3_bucket_public_access_block" "bucket" {
  bucket = aws_s3_bucket.bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Setting bucket ACL
resource "aws_s3_bucket_acl" "bucket" {
  depends_on = [
    aws_s3_bucket_ownership_controls.bucket,
    aws_s3_bucket_public_access_block.bucket,
  ]

  bucket = aws_s3_bucket.bucket.id
  acl    = "public-read"
}

# Creating a policy to the new user, so it can access the S3 resources
resource "aws_iam_policy" "s3_policy" {
  name        = "onlibrary-s3-policy" # Choose a name for the policy
  description = "Policy to allow required actions on the S3 resources"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:*"
        ],
        Effect = "Allow",
        Resource = [
          aws_s3_bucket.bucket.arn,
          "${aws_s3_bucket.bucket.arn}/*"
        ]
      }
    ]
  })
}

# Attaching the new policy to the user
resource "aws_iam_policy_attachment" "s3_attachment" {
  name       = "s3-policy-attachment" # Provide a name for the attachment
  policy_arn = aws_iam_policy.s3_policy.arn
  users      = [aws_iam_user.user.name]
}

# Creating a policy to the new user, so it can access SES resources
resource "aws_iam_policy" "ses_policy" {
  name        = "onlibrary-ses-policy" # Choose a name for the policy
  description = "Policy to allow sending emails via SES"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ],
        Effect   = "Allow",
        Resource = "*"
      }
    ]
  })
}

# Attaching the new policy to the user
resource "aws_iam_policy_attachment" "ses_attachment" {
  name       = "ses-policy-attachment"
  policy_arn = aws_iam_policy.ses_policy.arn
  users      = [aws_iam_user.user.name]
}

# Creating an access key for the newly created IAM user
# Access key ID and secret will be available at "terraform.tfstate" file
resource "aws_iam_access_key" "user" {
  user = aws_iam_user.user.name
}

# Defining a security group to access the EC2 instance to be created
resource "aws_security_group" "security_group" {
  name        = "onlibrary-security-group"
  description = "OnLibrary Security Group"

  # Allow SSH access from anywhere
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  # Allow HTTP access from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  # Allow HTTPS access from anywhere
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  # Allow MySQL (port 3306) access from anywhere
  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "MySQL"
  }

  # Outbound rule to allow all traffic to all destinations
  egress {
    from_port   = 0
    to_port     = 0    # Allow all ports
    protocol    = "-1" # Allow all protocols
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Defining variables for the EC2 instance user data
variable "user_password" {
  description = "User's password for the EC2 instance (write down this password, since it'll be the instance user's password)"
  type        = string
}
variable "ssh_public_key" {
  description = "SSH Public Key (formatted as: 'ssh-rsa PUBLIC_KEY_CONTENT', with no newlines) for the EC2 instance in order to access with the corresponding private key"
  type        = string
}

# Creating a new EC2 instance
resource "aws_instance" "ec2" {
  ami           = "ami-0e83be366243f524a" # Refers to Ubuntu Server 22.04 LTS (HVM), user data depends on it
  instance_type = "t3a.micro"             # You can replace this with your desired instance type

  # Defining the user data for the instance
  user_data = <<-EOF
    #!/bin/bash
    # Creating and setting up user
    useradd -m -s /bin/bash mhsw
    echo "mhsw:${var.user_password}" | chpasswd
    usermod -aG sudo mhsw
    mkdir -p /home/mhsw/.ssh
    echo "${var.ssh_public_key}" > /home/mhsw/.ssh/authorized_keys
    chmod 700 /home/mhsw/.ssh
    chmod 600 /home/mhsw/.ssh/authorized_keys
    chown -R mhsw:mhsw /home/mhsw/.ssh
    
    # Disable root login by editing the SSH configuration file
    sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    # Configure SSH to disable password authentication
    sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
    sudo service ssh restart
    
    # Install Python 3.9 using apt
    sudo apt update
    sudo apt install software-properties-common
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt install -y python3.9
    sudo apt install -y python3-pip
    sudo apt install -y python3.9-venv
    sudo pip install --upgrade pip
    # Install FFmpeg using apt
    sudo apt -y upgrade
    sudo apt install -y ffmpeg
    # Install make
    sudo apt -y install make
    # Install Nginx
    sudo apt -y install nginx
    # Install Certbot
    sudo apt -y install snapd
    sudo snap install core
    sudo snap refresh core
    sudo snap install --classic certbot
    sudo ln -s /snap/bin/certbot /usr/bin/certbot
    EOF

  # Adding the security group to the instance
  vpc_security_group_ids = [aws_security_group.security_group.id]
}

# Defining variables for the RDS instance user password
variable "db_password" {
  description = "User's password for the RDS instance (write down this password, since it'll be the database user's password)"
  type        = string
}

# Creating a new RDS database server instance
resource "aws_db_instance" "rds" {
  identifier            = "onlibrary"
  allocated_storage     = 20
  storage_type          = "gp3"
  engine                = "mysql"
  engine_version        = "8.0.33"
  instance_class        = "db.t3.micro"
  db_name               = "onlibrary"
  username              = "root"
  password              = var.db_password
  parameter_group_name  = "default.mysql8.0"
  publicly_accessible   = true
  skip_final_snapshot   = true
  storage_encrypted     = true
  copy_tags_to_snapshot = true

  # Enabling automated backups
  backup_retention_period = 7
  backup_window           = "03:50-04:20"

  # Adding the security group to the instance
  vpc_security_group_ids = [aws_security_group.security_group.id]
}
