# Autostart on reboot instructions

Copy cambridge_coffee_pot.service:
```
sudo cp cambridge_coffee_pot.service /etc/systemd/system/
```

Test start with:
```
sudo systemctl start cambridge_coffee_pot.service
```

## Set to run at boot time

```
sudo systemctl enable cambridge_coffee_pot.service
```
