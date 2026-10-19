#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NavigationPicker.generated.h"

UCLASS()
class ANavigationPicker : public AActor
{
    GENERATED_BODY()
public:
    ANavigationPicker();
    virtual void Tick(float DeltaSeconds) override;
private:
    FString Mailbox;
    int32 Sequence = 0;
    bool Selected = false;
    float Height = 2.f;
    FVector Target;
    class ACameraActor* MapCamera = nullptr;
    void Send(const FString& Action);
};
