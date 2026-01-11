-- MySQL dump 10.19  Distrib 10.3.39-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: biovarase
-- ------------------------------------------------------
-- Server version	10.3.39-MariaDB-0+deb10u2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `_org_migration_map`
--

DROP TABLE IF EXISTS `_org_migration_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `_org_migration_map` (
  `old_table` varchar(20) NOT NULL,
  `old_id` int(11) unsigned NOT NULL,
  `new_org_id` int(11) unsigned NOT NULL,
  PRIMARY KEY (`old_table`,`old_id`),
  KEY `idx_new_org_id` (`new_org_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `abbott_imported_files`
--

DROP TABLE IF EXISTS `abbott_imported_files`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `abbott_imported_files` (
  `file_id` int(11) NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) NOT NULL,
  `imported_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `records_count` int(11) DEFAULT 0,
  PRIMARY KEY (`file_id`),
  UNIQUE KEY `uk_filename` (`filename`),
  KEY `idx_imported_at` (`imported_at`)
) ENGINE=InnoDB AUTO_INCREMENT=2657 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `actions`
--

DROP TABLE IF EXISTS `actions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `actions` (
  `action_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `code` varchar(30) DEFAULT NULL,
  `description` varchar(50) NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`action_id`),
  UNIQUE KEY `unique_description` (`description`),
  KEY `idx_actions_status` (`status`),
  CONSTRAINT `chk_actions_status_valid` CHECK (`status` in (0,1))
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `audit_batches`
--

DROP TABLE IF EXISTS `audit_batches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `audit_batches` (
  `audit_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `operation` enum('INSERT','UPDATE','DELETE') NOT NULL,
  `batch_id` int(10) unsigned DEFAULT NULL,
  `lab_id` int(11) unsigned DEFAULT NULL COMMENT 'FK to labs.lab_id for multi-tenant audit filtering',
  `org_id` int(11) unsigned DEFAULT NULL COMMENT 'Organization ID for audit filtering',
  `control_id` smallint(5) unsigned DEFAULT NULL,
  `dict_test_id` mediumint(8) unsigned DEFAULT NULL,
  `workstation_id` tinyint(4) unsigned DEFAULT NULL,
  `lot_number` varchar(30) DEFAULT NULL,
  `expiration` date DEFAULT NULL,
  `target` decimal(12,4) unsigned DEFAULT NULL,
  `sd` decimal(12,6) unsigned DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  `lower` decimal(12,4) unsigned DEFAULT NULL,
  `upper` decimal(12,4) unsigned DEFAULT NULL,
  `rank` tinyint(3) unsigned DEFAULT NULL,
  `status` tinyint(1) unsigned DEFAULT NULL,
  `log_time` timestamp NOT NULL DEFAULT current_timestamp(),
  `log_id` smallint(6) DEFAULT NULL,
  `log_ip` varchar(15) DEFAULT NULL,
  PRIMARY KEY (`audit_id`),
  KEY `idx_audit_batches_batch_id_time` (`batch_id`,`log_time`),
  KEY `idx_audit_batches_user_time` (`log_id`,`log_time`),
  KEY `idx_audit_batch_id` (`batch_id`),
  KEY `idx_audit_log_time` (`log_time`),
  KEY `idx_audit_batch_time` (`batch_id`,`log_time`),
  KEY `idx_audit_user` (`log_id`),
  KEY `idx_audit_batches_lab_id` (`lab_id`),
  KEY `idx_audit_batches_lab_time` (`lab_id`,`log_time`),
  KEY `idx_audit_batches_org_id` (`org_id`)
) ENGINE=InnoDB AUTO_INCREMENT=9910 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `audit_results`
--

DROP TABLE IF EXISTS `audit_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `audit_results` (
  `audit_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `operation` enum('INSERT','UPDATE','DELETE') NOT NULL,
  `result_id` int(11) unsigned DEFAULT NULL,
  `lab_id` int(11) unsigned DEFAULT NULL COMMENT 'FK to labs.lab_id for multi-tenant audit filtering',
  `org_id` int(11) unsigned DEFAULT NULL COMMENT 'Organization ID for audit filtering',
  `batch_id` mediumint(11) unsigned DEFAULT NULL,
  `run_number` varchar(36) DEFAULT NULL,
  `workstation_id` tinyint(4) unsigned DEFAULT NULL,
  `reagent_lot` varchar(50) DEFAULT NULL COMMENT 'Reagent/kit lot number used for this measurement',
  `result` decimal(12,4) DEFAULT NULL,
  `received` timestamp NOT NULL DEFAULT current_timestamp(),
  `status` tinyint(1) unsigned DEFAULT NULL,
  `validated` tinyint(1) unsigned DEFAULT NULL,
  `validated_by` smallint(6) DEFAULT NULL,
  `validated_at` timestamp NULL DEFAULT NULL,
  `is_delete` tinyint(1) unsigned DEFAULT NULL,
  `log_time` timestamp NOT NULL DEFAULT current_timestamp(),
  `log_id` smallint(6) DEFAULT NULL,
  `log_ip` varchar(15) DEFAULT NULL,
  PRIMARY KEY (`audit_id`),
  KEY `idx_audit_results_result_id_time` (`result_id`,`log_time`),
  KEY `idx_audit_results_user_time` (`log_id`,`log_time`),
  KEY `idx_audit_result_id` (`result_id`),
  KEY `idx_audit_log_time` (`log_time`),
  KEY `idx_audit_result_time` (`result_id`,`log_time`),
  KEY `idx_audit_user` (`log_id`),
  KEY `idx_audit_results_lab_id` (`lab_id`),
  KEY `idx_audit_results_lab_time` (`lab_id`,`log_time`),
  KEY `idx_audit_results_org_id` (`org_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1370800 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `batches`
--

DROP TABLE IF EXISTS `batches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `batches` (
  `batch_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `lab_id` int(11) NOT NULL DEFAULT 0,
  `org_id` int(11) unsigned DEFAULT NULL COMMENT 'FK to organizations (lab level)',
  `control_id` tinyint(3) unsigned NOT NULL DEFAULT 8,
  `test_method_id` mediumint(8) unsigned DEFAULT NULL,
  `workstation_id` smallint(5) unsigned DEFAULT NULL,
  `lot_number` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `expiration` date DEFAULT NULL,
  `target` decimal(12,4) NOT NULL DEFAULT 0.0000,
  `sd` decimal(12,6) NOT NULL DEFAULT 0.000000,
  `description` varchar(255) NOT NULL DEFAULT 'NOT ASSIGNED',
  `lower` decimal(12,4) unsigned DEFAULT 0.0000,
  `upper` decimal(12,4) unsigned DEFAULT 0.0000,
  `rank` tinyint(3) unsigned DEFAULT 1,
  `status` tinyint(1) unsigned NOT NULL DEFAULT 1,
  `log_time` timestamp NOT NULL DEFAULT current_timestamp(),
  `log_id` smallint(6) DEFAULT 1,
  `log_ip` varchar(15) DEFAULT '127.0.0.1',
  PRIMARY KEY (`batch_id`),
  KEY `idx_batches_test_method_workstation_status` (`test_method_id`,`workstation_id`,`status`),
  KEY `idx_batches_expiration_status` (`expiration`,`status`),
  KEY `idx_batches_control` (`control_id`),
  KEY `idx_batches_lab` (`lab_id`),
  KEY `idx_batches_org_id` (`org_id`),
  CONSTRAINT `fk_batches_org` FOREIGN KEY (`org_id`) REFERENCES `organizations` (`org_id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6443 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER on_insert_batch
AFTER INSERT ON batches
FOR EACH ROW
BEGIN
    INSERT INTO audit_batches (
        operation,
        batch_id,
        lab_id,
        org_id,
        control_id,
        dict_test_id,
        workstation_id,
        lot_number,
        expiration,
        target,
        sd,
        description,
        `lower`,
        `upper`,
        `rank`,
        status,
        log_time,
        log_id,
        log_ip
    ) VALUES (
        'INSERT',
        NEW.batch_id,
        NEW.lab_id,
        NEW.org_id,
        NEW.control_id,
        NEW.test_method_id,
        NEW.workstation_id,
        NEW.lot_number,
        NEW.expiration,
        NEW.target,
        NEW.sd,
        NEW.description,
        NEW.lower,
        NEW.upper,
        NEW.rank,
        NEW.status,
        NOW(),
        NEW.log_id,
        NEW.log_ip
    );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER on_update_batch
AFTER UPDATE ON batches
FOR EACH ROW
BEGIN
    INSERT INTO audit_batches (
        operation,
        batch_id,
        lab_id,
        org_id,
        control_id,
        dict_test_id,
        workstation_id,
        lot_number,
        expiration,
        target,
        sd,
        description,
        `lower`,
        `upper`,
        `rank`,
        status,
        log_time,
        log_id,
        log_ip
    ) VALUES (
        'UPDATE',
        NEW.batch_id,
        NEW.lab_id,
        NEW.org_id,
        NEW.control_id,
        NEW.test_method_id,
        NEW.workstation_id,
        NEW.lot_number,
        NEW.expiration,
        NEW.target,
        NEW.sd,
        NEW.description,
        NEW.lower,
        NEW.upper,
        NEW.rank,
        NEW.status,
        NOW(),
        NEW.log_id,
        NEW.log_ip
    );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `categories` (
  `category_id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `lab_id` int(11) DEFAULT NULL,
  `org_id` int(11) unsigned DEFAULT NULL COMMENT 'FK to organizations (lab level)',
  `description` varchar(30) NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`category_id`),
  KEY `idx_categories_status` (`status`),
  KEY `idx_categories_lab` (`lab_id`),
  KEY `idx_categories_org_id` (`org_id`),
  CONSTRAINT `fk_categories_org` FOREIGN KEY (`org_id`) REFERENCES `organizations` (`org_id`) ON UPDATE CASCADE,
  CONSTRAINT `chk_categories_status_valid` CHECK (`status` in (0,1))
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `controls`
--

DROP TABLE IF EXISTS `controls`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `controls` (
  `control_id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `supplier_id` smallint(5) unsigned NOT NULL,
  `description` varchar(100) NOT NULL,
  `reference` varchar(30) DEFAULT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`control_id`),
  KEY `idx_controls_supplier_status` (`supplier_id`,`status`),
  CONSTRAINT `chk_controls_status_valid` CHECK (`status` in (0,1))
) ENGINE=InnoDB AUTO_INCREMENT=72 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `daily_approvals`
--

DROP TABLE IF EXISTS `daily_approvals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `daily_approvals` (
  `approval_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `approval_date` date NOT NULL,
  `workstation_id` smallint(5) unsigned NOT NULL,
  `approved_by` tinyint(3) unsigned NOT NULL,
  `approved_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `notes` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`approval_id`),
  UNIQUE KEY `uk_daily_ws` (`approval_date`,`workstation_id`),
  KEY `idx_approval_date` (`approval_date`),
  KEY `idx_workstation` (`workstation_id`),
  KEY `idx_approved_by` (`approved_by`),
  CONSTRAINT `fk_daily_approvals_user` FOREIGN KEY (`approved_by`) REFERENCES `users` (`user_id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_daily_approvals_workstation` FOREIGN KEY (`workstation_id`) REFERENCES `workstations` (`workstation_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dict_tests`
--

DROP TABLE IF EXISTS `dict_tests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dict_tests` (
  `dict_test_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `test_id` mediumint(8) unsigned NOT NULL,
  `category_id` smallint(5) unsigned DEFAULT NULL,
  `code` varchar(10) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `sample_id` tinyint(3) unsigned NOT NULL DEFAULT 0,
  `method_id` tinyint(3) unsigned NOT NULL DEFAULT 0,
  `unit_id` tinyint(3) unsigned NOT NULL DEFAULT 0,
  `section_id` mediumint(8) unsigned NOT NULL,
  `is_mandatory` tinyint(1) NOT NULL DEFAULT 1,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`dict_test_id`)
) ENGINE=InnoDB AUTO_INCREMENT=430 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `equipments`
--

DROP TABLE IF EXISTS `equipments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `equipments` (
  `equipment_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `supplier_id` smallint(5) unsigned DEFAULT 0,
  `description` varchar(100) DEFAULT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`equipment_id`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `goals`
--

DROP TABLE IF EXISTS `goals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `goals` (
  `goal_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `test_method_id` mediumint(8) unsigned NOT NULL,
  `cvw` float unsigned NOT NULL DEFAULT 0,
  `cvb` float unsigned NOT NULL DEFAULT 0,
  `imp` float unsigned NOT NULL DEFAULT 0,
  `bias` float unsigned NOT NULL DEFAULT 0,
  `teap005` float unsigned NOT NULL DEFAULT 0,
  `teap001` float unsigned NOT NULL DEFAULT 0,
  `to_export` tinyint(1) NOT NULL DEFAULT 0,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`goal_id`),
  KEY `idx_goals_test_method` (`test_method_id`),
  CONSTRAINT `fk_goals_test_method` FOREIGN KEY (`test_method_id`) REFERENCES `test_methods` (`test_method_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `labs`
--

DROP TABLE IF EXISTS `labs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `labs` (
  `lab_id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `site_id` tinyint(3) unsigned DEFAULT NULL,
  `user_id` tinyint(3) unsigned DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`lab_id`),
  UNIQUE KEY `unique_description_site` (`site_id`,`description`),
  KEY `idx_labs_site_status` (`site_id`,`status`),
  CONSTRAINT `fk_labs_site` FOREIGN KEY (`site_id`) REFERENCES `sites` (`site_id`) ON UPDATE CASCADE,
  CONSTRAINT `chk_labs_status_valid` CHECK (`status` in (0,1))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `methods`
--

DROP TABLE IF EXISTS `methods`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `methods` (
  `method_id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `description` varchar(30) NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`method_id`),
  UNIQUE KEY `unique_description` (`description`),
  KEY `idx_methods_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notes`
--

DROP TABLE IF EXISTS `notes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notes` (
  `note_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `result_id` int(10) unsigned NOT NULL,
  `action_id` smallint(5) unsigned NOT NULL,
  `description` varchar(200) NOT NULL,
  `modified` date NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`note_id`),
  KEY `result_id` (`result_id`),
  KEY `idx_notes_result_status` (`result_id`,`status`),
  KEY `idx_notes_action` (`action_id`),
  CONSTRAINT `chk_notes_status_valid` CHECK (`status` in (0,1))
) ENGINE=InnoDB AUTO_INCREMENT=230 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `organizations`
--

DROP TABLE IF EXISTS `organizations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `organizations` (
  `org_id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `parent_id` int(11) unsigned DEFAULT NULL COMMENT 'FK to parent org, NULL = root',
  `org_type` enum('country','region','site','lab','section') NOT NULL,
  `code` varchar(20) DEFAULT NULL COMMENT 'Short code (ITA, LAZ, etc.)',
  `description` varchar(255) NOT NULL,
  `status` tinyint(1) unsigned NOT NULL DEFAULT 1,
  PRIMARY KEY (`org_id`),
  KEY `idx_organizations_parent` (`parent_id`),
  KEY `idx_organizations_type` (`org_type`),
  CONSTRAINT `fk_organizations_parent` FOREIGN KEY (`parent_id`) REFERENCES `organizations` (`org_id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3011 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `results`
--

DROP TABLE IF EXISTS `results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `results` (
  `result_id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `batch_id` mediumint(11) unsigned NOT NULL,
  `lab_id` int(11) unsigned DEFAULT NULL COMMENT 'FK to labs.lab_id for multi-tenant isolation',
  `org_id` int(11) unsigned DEFAULT NULL COMMENT 'FK to organizations (lab level)',
  `run_number` varchar(36) NOT NULL DEFAULT '0',
  `workstation_id` smallint(5) unsigned NOT NULL,
  `reagent_lot` varchar(50) DEFAULT NULL COMMENT 'Reagent/kit lot number used for this measurement',
  `result` decimal(12,4) NOT NULL,
  `received` timestamp NOT NULL DEFAULT current_timestamp(),
  `status` tinyint(1) unsigned NOT NULL DEFAULT 1,
  `validated` tinyint(1) unsigned NOT NULL DEFAULT 0 COMMENT 'Validation flag: 0=pending, 1=validated',
  `validated_by` smallint(6) DEFAULT NULL COMMENT 'FK to users.user_id who validated the result',
  `validated_at` timestamp NULL DEFAULT NULL COMMENT 'Timestamp when result was validated',
  `is_delete` tinyint(1) NOT NULL DEFAULT 0,
  `log_time` timestamp NOT NULL DEFAULT current_timestamp(),
  `log_id` smallint(6) DEFAULT 1,
  `log_ip` varchar(15) DEFAULT '127.0.0.1',
  PRIMARY KEY (`result_id`),
  KEY `batch_idx` (`batch_id`),
  KEY `idx_results_validated` (`validated`,`received`),
  KEY `idx_results_validated_by` (`validated_by`),
  KEY `idx_results_batch_workstation_status` (`batch_id`,`workstation_id`,`status`,`is_delete`),
  KEY `idx_results_received_status` (`received`,`status`,`is_delete`),
  KEY `idx_results_lab_id` (`lab_id`),
  KEY `idx_results_lab_status` (`lab_id`,`status`,`is_delete`),
  KEY `idx_results_org_id` (`org_id`),
  CONSTRAINT `fk_results_lab` FOREIGN KEY (`lab_id`) REFERENCES `labs` (`lab_id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_results_org` FOREIGN KEY (`org_id`) REFERENCES `organizations` (`org_id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=669170 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER on_insert_results
AFTER INSERT ON results
FOR EACH ROW
BEGIN
    INSERT INTO audit_results (
        operation,
        result_id,
        lab_id,
        org_id,
        batch_id,
        run_number,
        workstation_id,
        result,
        received,
        status,
        validated,
        validated_by,
        validated_at,
        is_delete,
        log_time,
        log_id,
        log_ip
    ) VALUES (
        'INSERT',
        NEW.result_id,
        NEW.lab_id,
        NEW.org_id,
        NEW.batch_id,
        NEW.run_number,
        NEW.workstation_id,
        NEW.result,
        NEW.received,
        NEW.status,
        NEW.validated,
        NEW.validated_by,
        NEW.validated_at,
        NEW.is_delete,
        NOW(),
        NEW.log_id,
        NEW.log_ip
    );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER on_update_results
AFTER UPDATE ON results
FOR EACH ROW
BEGIN
    INSERT INTO audit_results (
        operation,
        result_id,
        lab_id,
        org_id,
        batch_id,
        run_number,
        workstation_id,
        result,
        received,
        status,
        validated,
        validated_by,
        validated_at,
        is_delete,
        log_time,
        log_id,
        log_ip
    ) VALUES (
        'UPDATE',
        NEW.result_id,
        NEW.lab_id,
        NEW.org_id,
        NEW.batch_id,
        NEW.run_number,
        NEW.workstation_id,
        NEW.result,
        NEW.received,
        NEW.status,
        NEW.validated,
        NEW.validated_by,
        NEW.validated_at,
        NEW.is_delete,
        NOW(),
        NEW.log_id,
        NEW.log_ip
    );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `samples`
--

DROP TABLE IF EXISTS `samples`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `samples` (
  `sample_id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `sample` varchar(1) NOT NULL,
  `description` varchar(8) NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`sample_id`),
  UNIQUE KEY `unique_description` (`description`),
  KEY `idx_samples_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sections`
--

DROP TABLE IF EXISTS `sections`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sections` (
  `section_id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `lab_id` tinyint(3) DEFAULT NULL,
  `user_id` tinyint(3) unsigned DEFAULT NULL,
  `description` varchar(255) NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`section_id`),
  UNIQUE KEY `unique_description_lab` (`lab_id`,`description`),
  KEY `idx_sections_lab_status` (`lab_id`,`status`),
  CONSTRAINT `chk_sections_status_valid` CHECK (`status` in (0,1))
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sites`
--

DROP TABLE IF EXISTS `sites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sites` (
  `site_id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `supplier_id` tinyint(4) DEFAULT NULL,
  `comp_id` tinyint(4) DEFAULT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`site_id`),
  KEY `idx_sites_status` (`status`),
  CONSTRAINT `chk_sites_status_valid` CHECK (`status` in (0,1))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `specialities`
--

DROP TABLE IF EXISTS `specialities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `specialities` (
  `speciality_id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `description` varchar(30) NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`speciality_id`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `suppliers`
--

DROP TABLE IF EXISTS `suppliers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `suppliers` (
  `supplier_id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `description` varchar(255) DEFAULT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`supplier_id`),
  UNIQUE KEY `unique_description` (`description`),
  KEY `idx_suppliers_status` (`status`),
  CONSTRAINT `chk_suppliers_status_valid` CHECK (`status` in (0,1))
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_methods`
--

DROP TABLE IF EXISTS `test_methods`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_methods` (
  `test_method_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `test_id` mediumint(8) unsigned NOT NULL,
  `category_id` smallint(5) unsigned DEFAULT NULL,
  `code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `sample_id` tinyint(3) unsigned NOT NULL DEFAULT 0,
  `method_id` tinyint(3) unsigned NOT NULL DEFAULT 0,
  `unit_id` tinyint(3) unsigned NOT NULL DEFAULT 0,
  `section_id` mediumint(8) unsigned NOT NULL,
  `lab_id` int(11) unsigned DEFAULT NULL COMMENT 'FK to labs.lab_id for multi-tenant isolation',
  `org_id` int(11) unsigned DEFAULT NULL COMMENT 'FK to organizations (section level)',
  `is_mandatory` tinyint(1) NOT NULL DEFAULT 1,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`test_method_id`),
  KEY `idx_test_methods_section_category_status` (`section_id`,`category_id`,`status`),
  KEY `idx_test_methods_test` (`test_id`),
  KEY `idx_test_methods_sample` (`sample_id`),
  KEY `idx_test_methods_method` (`method_id`),
  KEY `idx_test_methods_unit` (`unit_id`),
  KEY `idx_test_methods_lab_id` (`lab_id`),
  KEY `idx_test_methods_lab_status` (`lab_id`,`status`),
  KEY `idx_test_methods_org_id` (`org_id`),
  CONSTRAINT `fk_test_methods_lab` FOREIGN KEY (`lab_id`) REFERENCES `labs` (`lab_id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_test_methods_org` FOREIGN KEY (`org_id`) REFERENCES `organizations` (`org_id`) ON UPDATE CASCADE,
  CONSTRAINT `chk_test_methods_status_valid` CHECK (`status` in (0,1)),
  CONSTRAINT `chk_test_methods_is_mandatory_valid` CHECK (`is_mandatory` in (0,1)),
  CONSTRAINT `chk_test_methods_code_not_empty` CHECK (char_length(trim(`code`)) > 0)
) ENGINE=InnoDB AUTO_INCREMENT=1086 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tests`
--

DROP TABLE IF EXISTS `tests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tests` (
  `test_id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `description` varchar(255) NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`test_id`),
  UNIQUE KEY `unique_description` (`description`),
  KEY `idx_tests_status` (`status`),
  CONSTRAINT `chk_tests_status_valid` CHECK (`status` in (0,1)),
  CONSTRAINT `chk_tests_description_not_empty` CHECK (char_length(trim(`description`)) > 0)
) ENGINE=InnoDB AUTO_INCREMENT=1067 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `units`
--

DROP TABLE IF EXISTS `units`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `units` (
  `unit_id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `description` varchar(10) NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`unit_id`),
  KEY `idx_units_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=41 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `user_id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `last_name` varchar(35) NOT NULL,
  `first_name` varchar(35) DEFAULT NULL,
  `nickname` varchar(35) NOT NULL,
  `pswrd` varchar(255) NOT NULL,
  `role` tinyint(4) NOT NULL,
  `org_id` int(11) unsigned DEFAULT NULL COMMENT 'FK to organizations - defines user scope',
  `lab_id` tinyint(3) unsigned DEFAULT NULL,
  `elapsing_time` tinyint(4) NOT NULL DEFAULT 15,
  `enable_time` tinyint(1) NOT NULL DEFAULT 0,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`user_id`),
  KEY `idx_users_status` (`status`),
  KEY `idx_users_lab_id` (`lab_id`),
  KEY `idx_users_org_id` (`org_id`),
  CONSTRAINT `fk_users_org` FOREIGN KEY (`org_id`) REFERENCES `organizations` (`org_id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary table structure for view `vw_result_audit_history`
--

DROP TABLE IF EXISTS `vw_result_audit_history`;
/*!50001 DROP VIEW IF EXISTS `vw_result_audit_history`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `vw_result_audit_history` AS SELECT
 1 AS `audit_id`,
  1 AS `operation`,
  1 AS `result_id`,
  1 AS `result`,
  1 AS `received`,
  1 AS `status`,
  1 AS `validated`,
  1 AS `validated_at`,
  1 AS `log_time`,
  1 AS `user_id`,
  1 AS `changed_by`,
  1 AS `log_ip`,
  1 AS `lot_number`,
  1 AS `batch_description` */;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `workstation_test_methods`
--

DROP TABLE IF EXISTS `workstation_test_methods`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `workstation_test_methods` (
  `workstation_id` smallint(5) unsigned DEFAULT NULL,
  `test_method_id` mediumint(8) unsigned DEFAULT NULL,
  `external_code` varchar(50) DEFAULT NULL COMMENT 'Test code from workstation export (e.g., BHCG, FT4)',
  UNIQUE KEY `uk_wtm_external` (`workstation_id`,`external_code`),
  KEY `idx_wtm_test_method` (`test_method_id`),
  KEY `fk_wtm_workstation` (`workstation_id`),
  CONSTRAINT `fk_wtm_test_method` FOREIGN KEY (`test_method_id`) REFERENCES `test_methods` (`test_method_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_wtm_workstation` FOREIGN KEY (`workstation_id`) REFERENCES `workstations` (`workstation_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `workstations`
--

DROP TABLE IF EXISTS `workstations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `workstations` (
  `workstation_id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `equipment_id` smallint(5) unsigned NOT NULL,
  `device_id` varchar(36) NOT NULL,
  `description` varchar(36) NOT NULL,
  `serial` varchar(255) NOT NULL DEFAULT 'NOT ASSIGNED',
  `section_id` smallint(5) unsigned NOT NULL DEFAULT 1,
  `org_id` int(11) unsigned DEFAULT NULL COMMENT 'FK to organizations (section level)',
  `rank` tinyint(3) unsigned DEFAULT 1,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`workstation_id`),
  UNIQUE KEY `device_id` (`device_id`),
  KEY `idx_workstations_section_status_rank` (`section_id`,`status`,`rank`),
  KEY `idx_workstations_org_id` (`org_id`),
  CONSTRAINT `fk_workstations_org` FOREIGN KEY (`org_id`) REFERENCES `organizations` (`org_id`) ON UPDATE CASCADE,
  CONSTRAINT `chk_workstations_status_valid` CHECK (`status` in (0,1)),
  CONSTRAINT `chk_workstations_rank_valid` CHECK (`rank` >= 0 and `rank` <= 255)
) ENGINE=InnoDB AUTO_INCREMENT=48 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Final view structure for view `vw_result_audit_history`
--

/*!50001 DROP VIEW IF EXISTS `vw_result_audit_history`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_result_audit_history` AS select `ar`.`audit_id` AS `audit_id`,`ar`.`operation` AS `operation`,`ar`.`result_id` AS `result_id`,`ar`.`result` AS `result`,`ar`.`received` AS `received`,`ar`.`status` AS `status`,`ar`.`validated` AS `validated`,`ar`.`validated_at` AS `validated_at`,`ar`.`log_time` AS `log_time`,`u`.`user_id` AS `user_id`,concat(`u`.`first_name`,' ',`u`.`last_name`) AS `changed_by`,`ar`.`log_ip` AS `log_ip`,`b`.`lot_number` AS `lot_number`,`b`.`description` AS `batch_description` from ((`audit_results` `ar` left join `users` `u` on(`ar`.`log_id` = `u`.`user_id`)) left join `batches` `b` on(`ar`.`batch_id` = `b`.`batch_id`)) order by `ar`.`log_time` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-11 18:11:17
