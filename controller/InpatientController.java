package controller;

import com.medirecords.model.UserInfoDTO;
import com.medirecords.mrtemplatemicroservice.feign.MrFeatureToggleMicroserviceClient;
import com.medirecords.mrtemplatemicroservice.sample.feignclient.MrappClient;
import com.medirecords.userinjection.CurrentUserDetails;
import lombok.AllArgsConstructor;
import org.springframework.data.domain.Pageable;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;


@RestController
@AllArgsConstructor
@RequestMapping("/v1/api")
/** Template Controller exposes basic endpoints which to be used across different microservices */
public class TemplateController {
    private final CurrentUserDetails currentUser;
    private final MrappClient                       mrappClient;
    private final MrFeatureToggleMicroserviceClient featureToggleMicroserviceClient;

    @GetMapping("/hello")
    public ResponseEntity<String> hello(@RequestParam(value = "name", required = false, defaultValue = "stranger") String name) {
        String tenantName = this.currentUser.getTenantName();
        String userName = this.currentUser.getUserName();
        String tenantId = this.currentUser.getTenantId();
        String userId = this.currentUser.getUserId();
        return ResponseEntity.ok(String.format("Hello %s, this is hello from Template Microservice. "
                        + "Tenant id: %s. User id: %s. Tenant name: %s. User name: %s", name, tenantId, userId,
                tenantName, userName));
    }

    @GetMapping("/helloUserInfo")
    public ResponseEntity<UserInfoDTO> helloUserInfo(@RequestParam(value = "name", required = false, defaultValue = "stranger") String name) {
        UserInfoDTO userInfoDTO = new UserInfoDTO();
        userInfoDTO.setUserId(this.currentUser.getUserId());
        userInfoDTO.setUserName(this.currentUser.getUserName());
        userInfoDTO.setTenantId(this.currentUser.getTenantId());
        userInfoDTO.setTenantName(this.currentUser.getTenantName());
        return ResponseEntity.ok(userInfoDTO);
    }

    @GetMapping("/helloFeign")
    public ResponseEntity<String> helloFeign(Pageable pageable) {
        return ResponseEntity.ok(mrappClient.findAll(pageable));
    }

    @GetMapping("/helloFeatureToggle")
    public ResponseEntity<Boolean> helloFeatureToggleFeign() {
        return ResponseEntity.ok(featureToggleMicroserviceClient.checkTenantConfiguration("T", "UseTag", "76b011f6-25b3-11e7-a0ea-c776ddb51c38"));
    }
}
