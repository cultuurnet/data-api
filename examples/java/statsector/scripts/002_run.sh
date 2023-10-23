#!/bin/bash

export GOOGLE_APPLICATION_CREDENTIALS='sa/key.json'
mvn exec:java -Dexec.mainClass="be.publiq.StatsectorSampleApp"