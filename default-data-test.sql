INSERT INTO country VALUES
(1,'2020-01-01 00:00:00','2020-01-01 00:00:00','Brazil','BR');

INSERT INTO city VALUES
(1,'2020-01-01 00:00:00','2020-01-01 00:00:00','Brasília','DF',1);

INSERT INTO library VALUES
(1,'2020-01-01 00:00:00','2020-01-01 00:00:00','Library',NULL,NULL,1);

INSERT INTO role VALUES
(1,'2020-01-01 00:00:00','2020-01-01 00:00:00','Admin'),
(2,'2020-01-01 00:00:00','2020-01-01 00:00:00','Visitor');

INSERT INTO role_api_route VALUES
(1,'2020-01-01 00:00:00','2020-01-01 00:00:00','*','GET',1),
(2,'2020-01-01 00:00:00','2020-01-01 00:00:00','*','POST',1),
(3,'2020-01-01 00:00:00','2020-01-01 00:00:00','*','PUT',1),
(4,'2020-01-01 00:00:00','2020-01-01 00:00:00','*','PATCH',1),
(5,'2020-01-01 00:00:00','2020-01-01 00:00:00','*','DELETE',1),
(6,'2020-01-01 00:00:00','2020-01-01 00:00:00','*','GET',2);

INSERT INTO role_mobile_action VALUES
(1,'2020-01-01 00:00:00','2020-01-01 00:00:00','*',1);

INSERT INTO role_web_action VALUES
(1,'2020-01-01 00:00:00','2020-01-01 00:00:00','*',1);
