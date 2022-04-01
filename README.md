# edx-veripass
Proctortrack Veripass - Identity verification tool

## Overview
This is the student verification subsystem. This Python library provides the face and ID verificarion implementation used by Open edX.

## Dev Installation
To install edx-veripass:

``$ make lms-shell``

`` $ source /edx/app/edxapp/edxapp_env ``

`` $ pip install -e git+https://github.com/khushbu-07/edx-veripass.git@master#egg=edx-veripass ``



## Configuration
1. You will need to add new flag **ENABLE_VERIPASS** in /etc/lms.yml and /etc/cms.yml FEATURES dictionary:
```sh
"FEATURES": {
    :
    "ENABLE_VERIPASS": true,
    :
}
```

2. Add url in urls.py above **plugin_urls**
``` sh
if settings.FEATURES.get('ENABLE_VERIPASS', False):
    urlpatterns += [  
        url(r'', include('edx_veripass.urls', namespace='edx_veripass')),  
  	] 
```

3. Add middleware class in lms > env > common.py > MIDDLEWARE_CLASSES,
```sh
MIDDLEWARE_CLASSES = {
  ........
  # veripass enable for students
    'edx_veripass.middleware.VeripassMiddleware',
}
```
 
4. Add link in header after `SysAdmin` 

  `File: edx-platform/lms/templates/header/navbar-authenticated.html`


```sh
% if request.show_veripass:
    <div class="mobile-nav-item hidden-mobile nav-item nav-tab">  
      ## Translators: This is short for "Veripass".  
        <a class="tab-nav-link" href="${reverse('edx_veripass:veripass')}">${_("Veripass")}</a>  
    </div>  
% endif
```

5. You can call the Proctortrack veripass whenever student change their name on the platform.
```reverse('edx_veripass:veripass')```

6. You will need to **restart services** after these configuration changes for them to take effect.
This verification tool is for students only.

7. After restarting the service and login with student account, students can see  **Veripass**  link at header and can see verification dashboard as shown below.

 ![veripass dashboard](docs/images/edx-veripass.png) 

8. After uploading documents student can see uploading message on student dashboard and veripass dashboard.

![data uploaded msg](docs/images/data_uploaded.png) 

9. Once student Id and photo gets approved, student can see approval message on both student dashboard and veripass dashboard.

![approved message](docs/images/approve.png) 


<!-- <img src="edx-veripass.png"
     alt="Markdown Monster icon"
     style="float: left; margin-right: 10px; width: 500px; height: 300px;" /> -->

## Update Status on Open edX
Proctortrack will call an API to update the veripass result on edX. It will create and update the ManualVerification for the user to bypass the course verification.

**API Deatils:**
```sh
URL: /verified_results_callback
Method: POST
Result : {
  "user_email": "abc@example.com",
  "result": "submitted/pass/fail/system_fail", #Status of student veripass.
  "reason": "Reason for fail and system_fail status",
}

```


**NOTE**
  This will work only if you have configured Proctortrack settings in /etc/lms.yml and /etc/cms.yml.

  ```sh
  "PROCTORING_BACKENDS": {
      "null": {},
      "DEFAULT": "proctortrack",
      "proctortrack": {
          "account_id": "<registered account id of proctortrack account>",
          "client_id": "<proctortrack client id>",
          "client_secret": "<proctortrack client secret>",
          "base_url": "<proctortrack base url>" #"http://127.0.0.1:8000"
      }
  }, 
  ```

  * student will remain verified for 1 year(365 days). After expiration student need to reverify his/her identity.

## Getting Help
Have a question about this repository, or about Open edX in general? Please refer to this [list of resources](https://open.edx.org/community/connect) if you need any assistance.