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
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('br7qm40yiw985gow8k6fme8800js443y','.eJxVjM0OgjAQhN9lz6bBwvaHo3efgWy7W0ENNbScjO-uGC4cZ75v5g25voa1yAK9OcFAax3_cZgYejBw6ALFh8wb4DvNt6xinusyBbUpaqdFXTPL87K7h4ORyvhbY0qtpKDRtg0hsTQerWu97kwMkZtOC5K2wYt4OrvArJ1zUTvkaKxF-HwB-h88bg:1vsbo5:BV8lkOsOKr4gvBvtcc2hjzugH4_U4LFQ0Vu3Mm7pzNQ','2026-03-04 07:17:09.987224'),('jc7yqa3wpz3j1foz6zjwq4w8067a0r1i','.eJxVjEEOwiAQRe_C2pDCMEVcuvcMZGYAqZo2Ke3KeHdD0oVu_3vvv1Wkfatxb3mNU1IXher0uzHJM88dpAfN90XLMm_rxLor-qBN35aUX9fD_Tuo1GqvcXQUiLMrbFBgkFKSxQKjQ3BsvAVGzxaCCDCdgwGfg_gBORmLXn2-9GA3zg:1vqo89:iawunEj4oR8r7ojoqDPNhIW84-dLlVXw91OsAAHliIU','2026-02-27 08:02:25.249346'),('jijol0398rezjirlwsay58nwtlzw2581','.eJxVjDEOwjAMRe-SGUVOqjoJIztniOzYoQXUSk07Ie4OlTrA-t97_2UybeuQt6ZLHsWcjfPm9DsylYdOO5E7TbfZlnlal5HtrtiDNnudRZ-Xw_07GKgN37rzIYByqRKFBSorI5LromCfEDygV_KgqXcREVgIpbrYVZ9CIgzm_QEXjzgK:1vt11f:OeSULC532vVowDXLCDZc7dpLZam7SCTq-WFGZGz5TuI','2026-03-05 10:12:51.866787'),('nc9zl30tctvs2aefwo1exiqx6vivlplg','.eJxVjEEOwiAQRe_C2pAZKAgu3fcMZCiDVA0kpV0Z765NutDtf-_9lwi0rSVsnZcwJ3ERiOL0O0aaHlx3ku5Ub01Ora7LHOWuyIN2ObbEz-vh_h0U6uVbs3HJ-6i0y4BMVlt1Zg84gE0mZzUYwxkooyJLhNEBagTrIRo9KB3F-wPxrTcq:1vscKE:4Pw2JIIviRpYCWeigEdIrVcSg7bAoGqtZArz4YQnJhI','2026-03-04 07:50:22.977015'),('qjshhvis17vfw9gm6v6usoyy19h2l36a','.eJxVjMsOwiAQRf-FtSEIHR4u3fcbmoEZpGogKe3K-O_apAvd3nPOfYkJt7VMW-dlmklchBWn3y1ienDdAd2x3ppMra7LHOWuyIN2OTbi5_Vw_w4K9vKtIWfDOWpwRiEgsQrgvAl6sCkmUoNmQO1iYA549pFIe--T9kDJOgfi_QH1CDgd:1vsOvx:Hxd-KPC4vy5k49Uik6NPEtqEAxBYsCuskZs8sp-SBBU','2026-03-03 17:32:25.463009'),('rofyw6isvr871z4e9bu60qjf8vixj40v','.eJxVjEsOwjAMRO_iNYqaOG4IS_acobKdhBZQg_pZIe6Oirrpcua9mQ_U5d2tc57gQifoeF36f-yGBBcgOHTC-szjBtKDx3s1WsdlGsRsitnpbG415dd1dw8HPc_9tqbWc2TJvoglxUZLSY4Ktp7Qiw0OhYI4jKoofI4WQ44aGpJkHQX4_gD4yzwe:1vt01G:XGz0bfnhfLtx32r_uilvPztm7Yxsi8B0Fx8GZa9fC1Y','2026-03-05 09:08:22.773640');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-19 15:54:00
