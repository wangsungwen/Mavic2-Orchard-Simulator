#include "NavigationPicker.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"
#include "Engine/GameViewportClient.h"
#include "Kismet/GameplayStatics.h"
#include "DrawDebugHelpers.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "Serialization/JsonSerializer.h"
#include "SimMode/SimModeBase.h"

ANavigationPicker::ANavigationPicker()
{
    PrimaryActorTick.bCanEverTick = true;
    FParse::Value(FCommandLine::Get(), TEXT("NavMailbox="), Mailbox);
}

void ANavigationPicker::Send(const FString& Action)
{
    auto Sim = ASimModeBase::getSimMode();
    if (!Sim || !Sim->getApiProvider()) return;
    auto Vehicle = Sim->getVehicleSimApi("MavicSim");
    if (!Vehicle) return;
    auto Ned = Sim->getGlobalNedTransform().toGlobalNed(Target);
    TSharedRef<FJsonObject> Object = MakeShared<FJsonObject>();
    Object->SetNumberField(TEXT("sequence"), ++Sequence);
    Object->SetStringField(TEXT("action"), Action);
    Object->SetNumberField(TEXT("north"), Ned.x());
    Object->SetNumberField(TEXT("east"), Ned.y());
    Object->SetNumberField(TEXT("height"), Height);
    FString Json;
    auto Writer = TJsonWriterFactory<>::Create(&Json);
    FJsonSerializer::Serialize(Object, Writer);
    FFileHelper::SaveStringToFile(Json, *(Mailbox + TEXT(".tmp")));
    IFileManager::Get().Move(*Mailbox, *(Mailbox + TEXT(".tmp")), true);
}

void ANavigationPicker::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (Mailbox.IsEmpty()) return;
    auto PC = UGameplayStatics::GetPlayerController(this, 0);
    auto Sim = ASimModeBase::getSimMode();
    if (!PC || !Sim || !Sim->getApiProvider()) return;
    auto Vehicle = Sim->getVehicleSimApi("MavicSim");
    if (!Vehicle) return;
    if (!MapCamera) {
        MapCamera = GetWorld()->SpawnActor<ACameraActor>();
        FVector Origin = Sim->getGlobalNedTransform().fromGlobalNed(NedTransform::Vector3r(0,0,0));
        MapCamera->SetActorLocation(Origin + FVector(0,0,5000));
        MapCamera->SetActorRotation(FRotator(-90,0,0));
        MapCamera->GetCameraComponent()->SetProjectionMode(ECameraProjectionMode::Orthographic);
        MapCamera->GetCameraComponent()->SetOrthoWidth(3000);
        FInputModeGameOnly InputMode;
        InputMode.SetConsumeCaptureMouseDown(false);
        PC->SetInputMode(InputMode);
        if (GetWorld()->GetGameViewport())
            GetWorld()->GetGameViewport()->SetMouseCaptureMode(EMouseCaptureMode::CaptureDuringMouseDown);
        UE_LOG(LogTemp, Display, TEXT("NavigationPicker ready: %s"), *Mailbox);
    }
    PC->SetViewTarget(MapCamera);
    PC->bShowMouseCursor = true;
    // Camera navigation affects only the view, never aircraft commands.
    auto Camera = MapCamera->GetCameraComponent();
    float Width = Camera->OrthoWidth;
    if (PC->WasInputKeyJustPressed(EKeys::MouseScrollUp)) Width /= 1.2f;
    if (PC->WasInputKeyJustPressed(EKeys::MouseScrollDown)) Width *= 1.2f;
    FVector Location = MapCamera->GetActorLocation();
    int32 ViewX = 0, ViewY = 0;
    PC->GetViewportSize(ViewX, ViewY);
    const float Aspect = ViewY > 0 ? float(ViewX) / ViewY : 16.f / 9.f;
    Camera->bConstrainAspectRatio = false;
    if (PC->WasInputKeyJustPressed(EKeys::Home)) {
        Location = Sim->getGlobalNedTransform().fromGlobalNed(NedTransform::Vector3r(0,0,0)) + FVector(0,0,5000);
        Width = 3000.f;
    }
    if (PC->WasInputKeyJustPressed(EKeys::F)) {
        // Orchard terrain spans world XY [-5000,5000] cm.
        Location = FVector(0,0,15000) - FVector(GetWorld()->OriginLocation);
        Width = 11000.f * FMath::Max(1.f, Aspect);
    }
    Width = FMath::Clamp(Width, 1000.f, 30000.f);
    FVector Right = MapCamera->GetActorRightVector();
    FVector Up = MapCamera->GetActorUpVector();
    const float Step = Width * .6f * FMath::Min(DeltaSeconds, .1f);
    Location += Right * Step * (float(PC->IsInputKeyDown(EKeys::D)) - float(PC->IsInputKeyDown(EKeys::A)));
    Location += Up * Step * (float(PC->IsInputKeyDown(EKeys::W)) - float(PC->IsInputKeyDown(EKeys::S)));
    if (PC->IsInputKeyDown(EKeys::MiddleMouseButton)) {
        float DX=0, DY=0;
        PC->GetInputMouseDelta(DX,DY);
        const float UnitsPerPixel = Width / FMath::Max(1, ViewX);
        Location += (-Right * DX + Up * DY) * UnitsPerPixel;
    }
    const FVector WorldOrigin(GetWorld()->OriginLocation);
    Location.X = FMath::Clamp(Location.X, -10000.f-WorldOrigin.X, 10000.f-WorldOrigin.X);
    Location.Y = FMath::Clamp(Location.Y, -10000.f-WorldOrigin.Y, 10000.f-WorldOrigin.Y);
    MapCamera->SetActorLocation(Location);
    Camera->SetOrthoWidth(Width);
    if (PC->WasInputKeyJustReleased(EKeys::LeftMouseButton)) {
        FHitResult Hit;
        FVector RayStart, RayDirection;
        bool HasHit = false;
        if (PC->DeprojectMousePositionToWorld(RayStart, RayDirection)) {
            // Orthographic deprojection can start behind the floor. Start at
            // camera altitude and trace vertically through the selected XY.
            RayStart.Z = MapCamera->GetActorLocation().Z;
            HasHit = GetWorld()->LineTraceSingleByChannel(Hit, RayStart,
                RayStart + FVector(0,0,-100000), ECC_Visibility);
        }
        if (HasHit && Hit.ImpactNormal.Z > .8f) {
            Target = Hit.ImpactPoint;
            Selected = true;
        }
        UE_LOG(LogTemp, Display, TEXT("Navigation click: hit=%d location=%s"), HasHit, *Hit.ImpactPoint.ToString());
    }
    if (PC->WasInputKeyJustPressed(EKeys::Up)) Height = FMath::Min(10.f, Height + .5f);
    if (PC->WasInputKeyJustPressed(EKeys::Down)) Height = FMath::Max(1.f, Height - .5f);
    if (PC->WasInputKeyJustPressed(EKeys::X)) Send(TEXT("stop"));
    if (Selected && PC->WasInputKeyJustPressed(EKeys::Enter)) Send(TEXT("go"));
    FString Status;
    FFileHelper::LoadFileToString(Status, *(Mailbox + TEXT(".status")));
    if (GEngine) {
        GEngine->AddOnScreenDebugMessage(901, 0.f, FColor::Cyan,
            TEXT("AIRSIM ONLY | Click: select | Up/Down: height | Enter: fly | X: hover"));
        GEngine->AddOnScreenDebugMessage(904, 0.f, FColor::Cyan,
            TEXT("VIEW | Wheel: zoom | WASD / middle drag: pan | F: full map | Home: spawn | Flight radius: 20m"));
        GEngine->AddOnScreenDebugMessage(902, 0.f, FColor::Yellow,
            FString::Printf(TEXT("Height above starting vehicle: %.1f m | %s"), Height, *Status));
    }
    if (Selected) {
        auto Ned = Sim->getGlobalNedTransform().toGlobalNed(Target);
        DrawDebugSphere(GetWorld(), Target + FVector(0,0,20), 35, 16, FColor::Yellow, false, 0.f);
        if (GEngine) GEngine->AddOnScreenDebugMessage(903, 0.f, FColor::Green,
            FString::Printf(TEXT("Selected N=%.2f E=%.2f m | H=%.1f m | Enter to fly (straight segments)"), Ned.x(), Ned.y(), Height));
    }
}
