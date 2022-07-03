# Getting started

Install waybackpay, a tool used down download all 
website snapshots from archive.org

```bash
pip install waybackpack
```

Download the novelkeys archive.org snapshots using:

```bash
waybackpack https://novelkeys.com/pages/product-updates -d ~/Downloads/novelkeys-wayback

waybackpack https://novelkeys.xyz/pages/updates -d ~/Downloads/novelkeys-wayback
```

Remove a page that's just a redirect to novelkeys.com
```bash
rm ~/Downloads/novelkeys-wayback/20220617092711/novelkeys.xyz/pages/updates
```
