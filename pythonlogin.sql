CREATE DATABASE IF NOT EXISTS `pythonlogin` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `pythonlogin`;

CREATE TABLE IF NOT EXISTS `accounts` (
	`id` int(11) NOT NULL AUTO_INCREMENT,
  	`username` varchar(50) NOT NULL,
  	`password` varchar(255) NOT NULL,
  	`email` varchar(100) NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

INSERT INTO `accounts` (`id`, `username`, `password`, `email`) VALUES (1, 'test', 'test', 'test@test.com');

CREATE TABLE IF NOT EXISTS `pipelines` (
    `pipeline_id` int(11) NOT NULL AUTO_INCREMENT,
    `pipeline_name` varchar(50) NOT NULL,
    `client_id` int(11),
    `pipeline_status` varchar(20) NOT NULL,
    PRIMARY KEY (`pipeline_id`),
    FOREIGN KEY (`client_id`) REFERENCES accounts(`id`)
);

INSERT INTO `pipelines` (`pipeline_id`, `pipeline_name`, `client_id`, `pipeline_status`) VALUES (1, 'CloudFormation-CodePipelineProject', 1,'T');

INSERT INTO `accounts` (`id`, `username`, `password`, `email`) VALUES (2, 'test2', 'test2', 'test2@test.com');

INSERT INTO `accounts` (`id`, `username`, `password`, `email`) VALUES (3, 'test3', 'test3', 'test3@test.com');

INSERT INTO `pipelines` (`pipeline_id`, `pipeline_name`, `client_id`, `pipeline_status`) VALUES (2, 'kh_github', 2,'T');

INSERT INTO `pipelines` (`pipeline_id`, `pipeline_name`, `client_id`, `pipeline_status`) VALUES (3, 'github_pipeline', 2,'P');



