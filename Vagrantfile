# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|

  config.vm.define "web" do |web|
    web.vm.box = "ubuntu/xenial64"
    web.vm.synced_folder ".", "/vagrant"
    web.vm.provider "virtualbox" do |v|
      v.customize ["modifyvm", :id, "--hwvirtex", "off"]
      v.customize ["modifyvm", :id, "--vtxvpid", "off"]
      v.customize ["guestproperty", "set", :id, "--timesync-threshold", 10000]
      v.memory = 8192
      v.cpus = 4
    end
    web.vm.network "forwarded_port", guest: 14100, host: 14100 # Testnet
    web.vm.network "forwarded_port", guest: 4100, host: 4100 # Mainnet
  end
end
