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
-- Table structure for table `cars_car`
--

DROP TABLE IF EXISTS `cars_car`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cars_car` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `brand` varchar(100) NOT NULL,
  `car_type` varchar(50) NOT NULL,
  `location` varchar(100) NOT NULL,
  `price_per_day` decimal(10,2) NOT NULL,
  `seats` int NOT NULL,
  `image` varchar(100) DEFAULT NULL,
  `is_available` tinyint(1) NOT NULL,
  `status` varchar(10) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `owner_id` bigint NOT NULL,
  `is_featured` tinyint(1) NOT NULL,
  `thumbnail` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `cars_car_owner_id_1e7cce4a_fk_accounts_customuser_id` (`owner_id`),
  CONSTRAINT `cars_car_owner_id_1e7cce4a_fk_accounts_customuser_id` FOREIGN KEY (`owner_id`) REFERENCES `accounts_customuser` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cars_car`
--

LOCK TABLES `cars_car` WRITE;
/*!40000 ALTER TABLE `cars_car` DISABLE KEYS */;
INSERT INTO `cars_car` VALUES (7,'URUS','Lamborgini','Luxury','Jalandhar',15000.00,4,'car_images/urus.jpg',1,'approved','2026-02-20 17:23:20.322850',6,0,'car_thumbnails/urus_thumb.jpg'),(8,'PHANTOM','ROLLS-ROYCE','Luxury','PHAGWARA',30000.00,4,'car_images/phantom.jpg',1,'approved','2026-02-20 17:25:43.580438',6,0,'car_thumbnails/phantom_thumb.jpg'),(9,'911','PORCHE','Coupe','CHANDIGARH',12000.00,2,'car_images/urus_6N8rMr6.jpg',1,'approved','2026-02-20 17:27:10.235856',6,0,'car_thumbnails/urus_6N8rMr6_thumb.jpg'),(10,'Baleno','Maruti Suzuki','Hatchback','Ludhiana',2400.00,5,'car_images/baleno.jpg',1,'approved','2026-02-20 17:30:55.629434',5,0,'car_thumbnails/baleno_thumb.jpg'),(11,'VELLFIRE','TOYOTA','Luxury','HARDASPUR',8000.00,6,'car_images/vellfire.jpg',1,'approved','2026-02-20 17:32:20.775128',5,0,'car_thumbnails/vellfire_thumb.jpg');
/*!40000 ALTER TABLE `cars_car` ENABLE KEYS */;
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
