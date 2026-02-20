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
-- Table structure for table `notifications_notification`
--

DROP TABLE IF EXISTS `notifications_notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications_notification` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `message` longtext NOT NULL,
  `is_read` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `notifications_notifi_user_id_b5e8c0ff_fk_accounts_` (`user_id`),
  CONSTRAINT `notifications_notifi_user_id_b5e8c0ff_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_customuser` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications_notification`
--

LOCK TABLES `notifications_notification` WRITE;
/*!40000 ALTER TABLE `notifications_notification` DISABLE KEYS */;
INSERT INTO `notifications_notification` VALUES (1,'Payment received','Your payment for Honda City was received. Awaiting owner approval.',0,'2026-02-19 12:37:30.048094',5),(2,'New booking request','New booking request for Honda City from leo.',0,'2026-02-19 12:37:30.057093',6),(3,'Booking confirmed','Your booking for Honda City has been confirmed.',0,'2026-02-20 09:38:18.693584',5),(4,'Payment received','Your payment for lambo was received. Awaiting owner approval.',0,'2026-02-20 09:52:15.966104',16),(5,'New booking request','New booking request for lambo from sidhu.',0,'2026-02-20 09:52:16.049036',6),(6,'Booking rejected','Your booking for lambo was rejected.',0,'2026-02-20 09:55:35.893663',16),(7,'Payment received','Your payment for lambo was received. Awaiting owner approval.',0,'2026-02-20 16:49:41.712159',13),(8,'New booking request','New booking request for lambo from ashish.',0,'2026-02-20 16:49:41.761978',6),(9,'Payment received','Your payment for urus was received. Awaiting owner approval.',0,'2026-02-20 16:50:49.670423',13),(10,'New booking request','New booking request for urus from ashish.',0,'2026-02-20 16:50:49.721500',5),(11,'Booking confirmed','Your booking for urus has been confirmed.',0,'2026-02-20 16:53:10.616714',13),(12,'Booking confirmed','Your booking for lambo has been confirmed.',0,'2026-02-20 16:56:50.297146',13),(13,'Payment received','Your payment for URUS was received. Awaiting owner approval.',0,'2026-02-20 17:40:18.043609',13),(14,'New booking request','New booking request for URUS from ashish.',0,'2026-02-20 17:40:18.052143',6),(15,'Booking confirmed','Your booking for URUS has been confirmed.',0,'2026-02-20 17:44:25.462322',13);
/*!40000 ALTER TABLE `notifications_notification` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-20 23:49:31
