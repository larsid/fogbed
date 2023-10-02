# Monitoring Metrics
To enable the Prometheus monitoring and alerting service to access Fogbed metrics, set `metrics_enabled=True` in the experiment class:

```py title="topology.py"

from fogbed import Container, FogbedExperiment

exp = FogbedExperiment(metrics_enabled=True)
...

```
Fogbed uses Grafana to visualize and CAdvisor to collect data from all running workers. After the experiment starts you can access the Grafana Dashboard through the URL: <a href="http://localhost:3000/d/fogbed/docker-monitoring">http://localhost:3000/d/fogbed/docker-monitoring</a>. 

![dashboard](https://github.com/larsid/fogbed/assets/33939999/c30edaa9-5a20-4037-8313-ca2512125f82)

The default username and password are `admin` and `admin123`.