import {
  Button,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
} from "@chakra-ui/react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { useMutation, useQueryClient } from "react-query"

import { type ApiError, type ApiKeyCreate, ApiKeysService } from "../../client"
import useCustomToast from "../../hooks/useCustomToast"
import { useState } from "react"
import CopyInput from "../Common/CopyInput"

interface AddApiKeyProps {
  teamId: string,
  isOpen: boolean
  onClose: () => void
}

const AddApiKey = ({ teamId, isOpen, onClose }: AddApiKeyProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const [apiKey, setApiKey] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isValid },
  } = useForm<ApiKeyCreate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {},
  })

  const addApiKey = async (data: ApiKeyCreate) => {
    return await ApiKeysService.createApiKey({ requestBody: data, teamId: Number.parseInt(teamId) })
  }

  const mutation = useMutation(addApiKey, {
    onSuccess: (data) => {
      showToast("Успешно!", "API ключ успешно создан.", "success")
      setApiKey(data.key)
      reset()
    },
    onError: (err: ApiError) => {
      const errDetail = err.body?.detail
      showToast("Что-то пошло не так.", `${errDetail}`, "error")
    },
    onSettled: () => {
      queryClient.invalidateQueries("apikeys")
    },
  })

  const onSubmit: SubmitHandler<ApiKeyCreate> = (data) => {
    mutation.mutate(data)
  }

  const closeModalHandler = () => {
    onClose()
    setApiKey(null)
  }

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        size={{ base: "sm", md: "md" }}
        isCentered
        closeOnOverlayClick={false}
      >
        <ModalOverlay />
       {!apiKey ? <ModalContent as="form" onSubmit={handleSubmit(onSubmit)}>
          <ModalHeader>Создать API ключ</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <FormControl isInvalid={!!errors.description}>
              <FormLabel htmlFor="description">Описание</FormLabel>
              <Input
                id="description"
                {...register("description")}
                placeholder="Описание..."
                type="text"
              />
              {errors.description && (
                <FormErrorMessage>{errors.description.message}</FormErrorMessage>
              )}
            </FormControl>
          </ModalBody>
          <ModalFooter gap={3}>
            <Button
              variant="primary"
              type="submit"
              isLoading={isSubmitting || mutation.isLoading}
              isDisabled={!isValid}
            >
              Создать API ключ
            </Button>
            <Button onClick={onClose}>Отмена</Button>
          </ModalFooter>
        </ModalContent> : <ModalContent as="form" onSubmit={handleSubmit(onSubmit)}>
          <ModalHeader>Скопируйте ваш новый API ключ</ModalHeader>
          <ModalBody pb={6}>
            <CopyInput value={apiKey} />
          </ModalBody>
          <ModalFooter gap={3}>
            <Button
              onClick={closeModalHandler}
            >
              Я сохранил API ключ в надежном месте
            </Button>
          </ModalFooter>
        </ModalContent>}
      </Modal>
    </>
  )
}

export default AddApiKey
