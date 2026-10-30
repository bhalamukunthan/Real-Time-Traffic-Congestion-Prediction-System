@echo off
title SmartTraffic AI - Kafka Telemetry Producer
echo ================================================================
echo Starting Traffic Event Producer (Topic: traffic-events)
echo Streaming interval: 2.0 seconds
echo ================================================================
python streaming\producer.py --interval 2.0
pause

