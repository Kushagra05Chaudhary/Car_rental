-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: car_rental
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-02-13 06:28:37.067528'),(2,'contenttypes','0002_remove_content_type_name','2026-02-13 06:28:37.239262'),(3,'auth','0001_initial','2026-02-13 06:28:37.889992'),(4,'auth','0002_alter_permission_name_max_length','2026-02-13 06:28:37.994213'),(5,'auth','0003_alter_user_email_max_length','2026-02-13 06:28:38.003391'),(6,'auth','0004_alter_user_username_opts','2026-02-13 06:28:38.011392'),(7,'auth','0005_alter_user_last_login_null','2026-02-13 06:28:38.020505'),(8,'auth','0006_require_contenttypes_0002','2026-02-13 06:28:38.027183'),(9,'auth','0007_alter_validators_add_error_messages','2026-02-13 06:28:38.038413'),(10,'auth','0008_alter_user_username_max_length','2026-02-13 06:28:38.047779'),(11,'auth','0009_alter_user_last_name_max_length','2026-02-13 06:28:38.057123'),(12,'auth','0010_alter_group_name_max_length','2026-02-13 06:28:38.079546'),(13,'auth','0011_update_proxy_permissions','2026-02-13 06:28:38.090295'),(14,'auth','0012_alter_user_first_name_max_length','2026-02-13 06:28:38.099299'),(15,'accounts','0001_initial','2026-02-13 06:28:38.697323'),(16,'accounts','0002_customuser_is_email_verified','2026-02-13 06:28:38.810254'),(17,'accounts','0003_otp','2026-02-13 06:28:38.956161'),(18,'accounts','0004_alter_customuser_role','2026-02-13 06:28:38.967225'),(19,'admin','0001_initial','2026-02-13 06:28:39.244486'),(20,'admin','0002_logentry_remove_auto_add','2026-02-13 06:28:39.256347'),(21,'admin','0003_logentry_add_action_flag_choices','2026-02-13 06:28:39.268346'),(22,'sessions','0001_initial','2026-02-13 06:28:39.337448'),(23,'accounts','0005_ownerrequest','2026-02-17 10:56:02.282577'),(25,'cars','0001_initial','2026-02-17 17:28:48.288203'),(26,'accounts','0006_customuser_created_at_customuser_driving_license_and_more','2026-02-18 05:40:08.903669'),(27,'bookings','0001_initial','2026-02-18 05:40:09.296618'),(28,'payments','0001_initial','2026-02-18 05:40:09.582711'),(29,'reports','0001_initial','2026-02-18 05:40:09.740046'),(30,'accounts','0007_ownerrequest_rejection_reason','2026-02-19 08:49:51.590283'),(31,'cars','0002_car_is_featured','2026-02-19 08:49:51.688637'),(33,'bookings','0002_booking_hold','2026-02-19 10:12:30.314430'),(34,'notifications','0001_initial','2026-02-19 10:12:30.454984'),(35,'reviews','0001_initial','2026-02-19 11:13:27.878846'),(36,'cars','0002_add_thumbnail_to_car','2026-02-19 13:24:18.665419'),(37,'cars','0003_merge_0002_add_thumbnail_to_car_0002_car_is_featured','2026-02-19 16:59:38.346216');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-20 23:49:30
