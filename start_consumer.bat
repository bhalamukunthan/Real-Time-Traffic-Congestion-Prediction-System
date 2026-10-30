@echo off
title SmartTraffic AI - Kafka Consumer & Stream Processor
echo ================================================================
echo Starting Traffic Event Consumer (Topic: traffic-events)
echo Processing sliding windows, ML predictions, and DB persistence...
echo ================================================================
python streaming\consumer.py
pause

