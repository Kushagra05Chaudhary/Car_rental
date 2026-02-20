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
-- Table structure for table `accounts_customuser`
--

DROP TABLE IF EXISTS `accounts_customuser`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_customuser` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `role` varchar(10) NOT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `is_email_verified` tinyint(1) NOT NULL,
  `created_at` datetime(6) DEFAULT NULL,
  `driving_license` varchar(100) DEFAULT NULL,
  `insurance_document` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_customuser`
--

LOCK TABLES `accounts_customuser` WRITE;
/*!40000 ALTER TABLE `accounts_customuser` DISABLE KEYS */;
INSERT INTO `accounts_customuser` VALUES (2,'pbkdf2_sha256$1000000$xnkeQtDL70qPKkNmeEvWCb$3zmFcZ7SbKiDkzuJY7XBIfvsweeaV2Uy3AbvehYjYQs=','2026-02-17 10:59:19.986709',1,'kushagra','','','kush.c47007@gmail.com',1,1,'2026-02-13 07:05:29.361983','user',NULL,0,'2026-02-18 05:40:08.724160',NULL,NULL),(5,'pbkdf2_sha256$1000000$WlPOaj7bcZr355hOhJC8a5$hajmCfh2xkR4EAhEdCaDjN26Qj8cnsN/epvGahM/7oo=','2026-02-19 09:08:22.766752',0,'leo','','','demon.d.leo1170013@gmail.com',0,1,'2026-02-13 08:02:24.926798','user','09506289312',1,'2026-02-18 05:40:08.724160',NULL,NULL),(6,'pbkdf2_sha256$1000000$pX5XKr1Mgpmkibk2Id8ZxK$wQOzjgETFe4bZ98NpeT639N51PoJg16EBXiwSTRkhV0=','2026-02-18 07:17:09.967410',0,'alok','','','alok.work85@gmail.com',0,1,'2026-02-17 10:57:48.515650','owner','7970820876',1,'2026-02-18 05:40:08.724160',NULL,NULL),(7,'pbkdf2_sha256$1000000$ZT9qRqjodChjQaK8MmmXjC$UyNsBugyQsUxy+2hAhR80oC9Ud+qb0+2u6b/MDvnyxE=','2026-02-18 05:11:40.168356',1,'kush','','','kush.c47007@gmail.com',1,1,'2026-02-17 11:00:43.648081','owner',NULL,0,'2026-02-18 05:40:08.724160',NULL,NULL),(8,'pbkdf2_sha256$1000000$nVx0Ytn3lYxWiaFfi4nMgM$TgXtpy1mnrjevK8d1pJ2dNpN1lJOL6oR3FbE8TpgGT8=','2026-02-17 16:51:37.102420',0,'aaloo','','','test.work5681@gmail.com',0,1,'2026-02-17 16:51:34.025941','user','9876543210',1,'2026-02-18 05:40:08.724160',NULL,NULL),(9,'pbkdf2_sha256$1000000$98sAaBKTNj1eo3tpJ3FQ8t$DjBy8EibLdptVkUMQJkKUbN2WVYlz/NB15qQEg57Zps=','2026-02-18 06:02:58.240204',0,'shubh','','','shubhsahu2006@gmail.com',0,1,'2026-02-18 04:52:19.928754','owner','6261248251',1,'2026-02-18 05:40:08.724160',NULL,NULL),(10,'!dpL50NQv9JvMupRZT1rG50C5Kn74DITaorxF2bZb',NULL,0,'shubh123','','','',0,1,'2026-02-18 05:12:14.622619','user',NULL,0,'2026-02-18 05:40:08.724160',NULL,NULL),(11,'pbkdf2_sha256$1000000$KmXXnIrFfwsiJc1Z6Ju7nW$SZ9Q8Xesec5SvKX9LsJ8p0SW4OL3I5CFUEQu+11circ=','2026-02-19 09:59:04.837665',1,'super','','','shubhsahu2005@gmail.com',1,1,'2026-02-18 05:13:58.501689','owner',NULL,0,'2026-02-18 05:40:08.724160','',''),(12,'pbkdf2_sha256$1000000$pdMFq3uSRScGN5U5HiVj6J$kKrYhacPVNO2uM4nkRTt+pZbajJgMFBgN1Ke6JJ6pY0=','2026-02-19 10:12:51.847785',0,'ptanhi','','','',0,1,'2026-02-19 09:58:08.000000','user',NULL,0,'2026-02-19 09:58:09.012616','','');
/*!40000 ALTER TABLE `accounts_customuser` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-19 15:53:59
