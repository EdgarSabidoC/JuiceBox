# Servicio Juice Box WebClient

## Estado del servicio

Para ver el estado del servicio de `sytemd` solo basta con ejecutar:

```bash
systemctl status juiceboxweb
```

## Logs del servicio

### Logs en tiempo real

Para ver los logs en tiempo real solo basta con ejecutar:

```bash
journalctl -u juiceboxweb -f
```